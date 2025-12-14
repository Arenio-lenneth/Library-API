# ==================================================
# LIBRARY API (JSON + XML)
# Flask + MySQL + JWT + Session
# Restaurant-style clean structure
# ==================================================

from flask import Flask, request, jsonify, render_template_string, session
from flask_bcrypt import Bcrypt
from functools import wraps
import datetime
import jwt
import mysql.connector
import xml.etree.ElementTree as ET
from mysql.connector import Error


# ==================================================
# APP SETUP
# ==================================================
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config.update(SECRET_KEY="supersecretkey", JWT_EXP_HOURS=2)

# ==================================================
# DATABASE CONFIG
# ==================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "library_db"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ==================================================
# DB INIT
# ==================================================

def init_db():
    db = get_db(); cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password VARCHAR(255)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS authors (
        author_id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(100),
        last_name VARCHAR(100)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        book_id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        author_id INT,
        genre VARCHAR(100),
        publish_year INT,
        available_copies INT,
        date_added DATE,
        FOREIGN KEY (author_id) REFERENCES authors(author_id)
    )""")

    db.commit(); db.close()

# ==================================================
# XML + RESPONSE HELPER
# ==================================================

def to_xml(data, root="items"):
    root_el = ET.Element(root)
    for row in data:
        item = ET.SubElement(root_el, "item")
        for k, v in row.items():
            ET.SubElement(item, k).text = str(v)
    return ET.tostring(root_el, encoding="utf-8")


def respond(data, root="items"):
    fmt = request.args.get("format", "").lower()
    accept = request.headers.get("Accept", "").lower()

    # Explicit XML
    if fmt == "xml":
        return app.response_class(
            to_xml(data, root),
            mimetype="application/xml"
        )

    # Explicit JSON
    if fmt == "json":
        return jsonify(data)

    # Header-based fallback
    if "application/xml" in accept:
        return app.response_class(
            to_xml(data, root),
            mimetype="application/xml"
        )

    return jsonify(data)


# ==================================================
# JWT DECORATOR
# ==================================================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
        else:
            token = session.get("token")

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)
    return decorated

# ==================================================
# AUTH
# ==================================================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "GET":
        return """
        <style>
        body{background:#121212;color:#fff;font-family:Segoe UI;padding:40px}
        input{padding:8px;width:250px}
        button{background:#ff4d8d;color:white;padding:8px 16px;border-radius:8px}
        </style>
        <h2>Register</h2>
        <form method="POST">
            <input name="username" placeholder="Username" required><br><br>
            <input name="password" type="password" placeholder="Password" required><br><br>
            <button>Register</button>
        </form>
        """

    username = request.form["username"]
    password = request.form["password"]

    db = get_db()
    cur = db.cursor(dictionary=True)

    try:
        pw = bcrypt.generate_password_hash(password).decode()
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, pw)
        )
        db.commit()

    except Error as e:
        # 🔴 DUPLICATE USERNAME
        if e.errno == 1062:
            return """
            <style>
            body{background:#121212;color:#fff;font-family:Segoe UI;padding:40px}
            a{color:#ff4d8d}
            </style>
            <h3>⚠ Username already exists</h3>
            <p>Please choose a different username.</p>
            <a href="/register">← Try again</a>
            """

        # 🔴 OTHER DB ERRORS
        return f"<h3>Database error: {e}</h3>"

    finally:
        db.close()

    return """
    <style>
    body{background:#121212;color:#fff;font-family:Segoe UI;padding:40px}
    a{color:#ff4d8d}
    </style>
    <h3>✅ Registration successful</h3>
    <a href="/login">Go to Login</a>
    """



@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return """
        <style>
        body{
            background:#121212;
            color:#fff;
            font-family:Segoe UI;
            padding:40px
        }
        input{
            padding:10px;
            width:260px;
            background:#1e1e1e;
            color:#fff;
            border:1px solid #333;
            border-radius:8px
        }
        button{
            background:#ff4d8d;
            color:white;
            padding:10px 18px;
            border-radius:10px;
            border:none;
            font-weight:600;
            cursor:pointer
        }
        textarea{
            width:100%;
            max-width:600px;
            height:120px;
            background:#1e1e1e;
            color:#00ffcc;
            border-radius:10px;
            border:1px solid #333;
            padding:12px
        }
        </style>

        <h2>Login</h2>
        <form method="POST">
            <input name="username" placeholder="Username" required><br><br>
            <input name="password" type="password" placeholder="Password" required><br><br>
            <button>Login</button>
        </form>
        """

    # ---------- LOGIN LOGIC ----------
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE username=%s", (request.form["username"],))
    user = cur.fetchone()
    db.close()

    if not user or not bcrypt.check_password_hash(
        user["password"], request.form["password"]
    ):
        return "<h3>Invalid credentials</h3>"

    token = jwt.encode(
        {
            "user": user["username"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    # 🔐 save in session
    session["token"] = token

    # ---------- DISPLAY TOKEN ----------
    return f"""
    <style>
    body{{background:#121212;color:#fff;font-family:Segoe UI;padding:40px}}
    textarea{{width:100%;max-width:600px;height:120px;
              background:#1e1e1e;color:#00ffcc;
              border-radius:10px;padding:12px}}
    a{{color:#ff4d8d;font-weight:600}}
    </style>

    <h2>✅ Login Successful</h2>

    <p><b>Your JWT Token:</b></p>
    <textarea readonly>{token}</textarea>

    <br><br>
    <a href="/books">📚 Go to Books</a>
    """


# ==================================================
# BOOKS (HTML + JSON + XML)
# ==================================================
@app.route("/books")
@token_required
def books():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT b.book_id, b.title,
        CONCAT(a.first_name,' ',a.last_name) AS author,
        b.genre, b.publish_year, b.available_copies
        FROM books b JOIN authors a ON b.author_id=a.author_id
    """)
    data = cur.fetchall(); db.close()

    if request.args.get("format") or "application/json" in request.headers.get("Accept", ""):
        return respond(data, "books")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Library Books</title>
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: #121212;
            color: #e0e0e0;
            padding: 30px;
        }

        h1 {
            color: #ffffff;
            margin-bottom: 15px;
        }

        a {
            text-decoration: none;
            color: #cfcfcf;
        }

        a:hover {
            color: #ffffff;
        }

        /* 🔴 BUTTON ONLY PINK */
        .btn-pink {
            display: inline-block;
            background-color: #ff4d8d;
            color: #fff;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            margin-bottom: 25px;
        }

        .btn-pink:hover {
            background-color: #e13c77;
        }

        .book {
            background-color: #1e1e1e;
            border-radius: 12px;
            padding: 16px 22px;
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.6);
        }

        .book-title {
            font-size: 17px;
            font-weight: 600;
            color: #ffffff;
        }

        .book-meta {
            font-size: 14px;
            color: #aaaaaa;
            margin-top: 4px;
        }

        .actions a {
            margin-left: 12px;
            font-size: 18px;
            color: #bbbbbb;
        }

        .actions a:hover {
            color: #ffffff;
        }
    </style>
</head>

<body>
    <h1>📚 Library Books</h1>

    <!-- PINK BUTTON -->
    <a class="btn-pink" href="/books/add">➕ Add Book</a>

    {% for b in books %}
    <div class="book">
        <div>
            <div class="book-title">{{ b.title }}</div>
            <div class="book-meta">
                {{ b.author }} • {{ b.genre }} • {{ b.publish_year }}
            </div>
        </div>

        <div class="actions">
            <a href="/books/edit/{{ b.book_id }}">✏️</a>
            <a href="/books/delete/{{ b.book_id }}"
               onclick="return confirm('Delete this book?')">🗑</a>
        </div>
    </div>
    {% endfor %}
</body>
</html>
""", books=data)

@app.route("/authors")
@token_required
def authors():
    db = get_db(); cur = db.cursor(dictionary=True)
    cur.execute("SELECT * FROM authors")
    data = cur.fetchall(); db.close()

    if request.args.get("format") or "application/json" in request.headers.get("Accept",""):
        return respond(data, "authors")

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Authors</title>
<style>
body { background:#121212; color:#e0e0e0; font-family:Segoe UI; padding:30px }
.card { background:#1e1e1e; padding:15px; border-radius:10px; margin-bottom:10px }
.btn { background:#ff4d8d; color:white; padding:8px 14px; border-radius:8px }
</style>
</head>
<body>
<h1>✍️ Authors</h1>
<a class="btn" href="/authors/add">➕ Add Author</a><br><br>
{% for a in authors %}
<div class="card">
{{ a.first_name }} {{ a.last_name }}
</div>
{% endfor %}
</body>
</html>
""", authors=data)

@app.route("/authors/add", methods=["GET","POST"])
@token_required
def add_author_page(): 

    if request.method == "GET":
        return """
        <style>
        body{background:#121212;color:#fff;font-family:Segoe UI;padding:30px}
        button{background:#ff4d8d;color:white;padding:8px 14px;border-radius:8px}
        </style>
        <h2>Add Author</h2>
        <form method="POST">
            <input name="first_name" placeholder="First Name"><br><br>
            <input name="last_name" placeholder="Last Name"><br><br>
            <button>Add</button>
        </form>
        """

    db = get_db(); cur = db.cursor()
    cur.execute("INSERT INTO authors (first_name,last_name) VALUES (%s,%s)",
                (request.form["first_name"], request.form["last_name"]))
    db.commit(); db.close()
    return "<a href='/authors'>Back</a>"

@app.route("/books/search")
@token_required
def search_books():
    q = request.args.get("q", "").strip()

    # 🚫 prevent empty search
    if not q:
        return render_template_string("""
        <style>
        body{background:#121212;color:#fff;font-family:Segoe UI;padding:30px}
        a{color:#ff4d8d}
        </style>

        <h3>⚠ Please enter a search term</h3>
        <a href="/books">← Back to Books</a>
        """)

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT b.book_id, b.title,
               CONCAT(a.first_name,' ',a.last_name) AS author,
               b.genre, b.publish_year
        FROM books b
        JOIN authors a ON b.author_id=a.author_id
        WHERE b.title LIKE %s OR b.genre LIKE %s
    """, (f"%{q}%", f"%{q}%"))

    data = cur.fetchall()
    db.close()

    return render_template_string("""
    <style>
        body{background:#121212;color:#fff;font-family:Segoe UI;padding:30px}
        .card{background:#1e1e1e;padding:15px;border-radius:10px;margin-bottom:10px}
        a{color:#ff4d8d}
    </style>

    <h2>🔍 Search Results for "{{ q }}"</h2>
    <a href="/books">← Back to Books</a><br><br>

    {% if books %}
        {% for b in books %}
        <div class="card">
            <b>{{ b.title }}</b><br>
            {{ b.author }} • {{ b.genre }} • {{ b.publish_year }}
        </div>
        {% endfor %}
    {% else %}
        <p>No matching books found.</p>
    {% endif %}
    """, books=data, q=q)




# ==================================================
# CRUD (BROWSER)
# ==================================================
@app.route("/books/add", methods=["GET","POST"])
@token_required
def add_book():
    if request.method == "GET":
        return """
        <style>
        body{background:#121212;color:#fff;font-family:Segoe UI;padding:30px}
        input{padding:8px;width:250px}
        button{background:#ff4d8d;color:white;padding:8px 16px;border-radius:8px}
        </style>
        <h2>Add Book</h2>
        <form method="POST">
            <input name="title" placeholder="Title"><br><br>
            <input name="author_id" placeholder="Author ID"><br><br>
            <input name="genre" placeholder="Genre"><br><br>
            <input name="publish_year" placeholder="Year"><br><br>
            <input name="available_copies" placeholder="Copies"><br><br>
            <button>Add</button>
        </form>
        """


    db = get_db(); cur = db.cursor()
    cur.execute("""
        INSERT INTO books
        (title,author_id,genre,publish_year,available_copies,date_added)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        request.form["title"], request.form["author_id"], request.form["genre"],
        request.form["publish_year"], request.form["available_copies"], datetime.date.today()
    ))
    db.commit(); db.close()
    return "<h3>Book Added</h3><a href='/books'>Back</a>"


@app.route("/books/edit/<int:id>", methods=["GET", "POST"])
@token_required
def edit_book(id):
    db = get_db(); cur = db.cursor(dictionary=True)

    if request.method == "GET":
        cur.execute("SELECT * FROM books WHERE book_id=%s", (id,))
        book = cur.fetchone(); db.close()
        return f"""
        <h2>Edit Book</h2>
        <form method="POST">
            <input name="title" value="{book['title']}"><br><br>
            <input name="genre" value="{book['genre']}"><br><br>
            <input name="available_copies" value="{book['available_copies']}"><br><br>
            <button>Update</button>
        </form>"""

    cur.execute("""
        UPDATE books SET title=%s, genre=%s, available_copies=%s
        WHERE book_id=%s
    """, (
        request.form["title"], request.form["genre"], request.form["available_copies"], id
    ))
    db.commit(); db.close()
    return "<h3>Updated</h3><a href='/books'>Back</a>"

@app.route("/books/delete/<int:id>")
@token_required
def delete_book(id):
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM books WHERE book_id=%s", (id,))
    db.commit(); db.close()
    return "<h3>Deleted</h3><a href='/books'>Back</a>"

# ==================================================
# HOME + RUN
# ==================================================
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Library API</title>
    <style>
        body {
            margin: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0f0f, #1a1a1a);
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .container {
            background: #161616;
            border-radius: 16px;
            padding: 40px 50px;
            width: 420px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.7);
            text-align: center;
        }

        h1 {
            margin-bottom: 10px;
            font-size: 28px;
            color: #ffffff;
        }

        .subtitle {
            font-size: 14px;
            color: #aaaaaa;
            margin-bottom: 30px;
        }

        .btn {
            display: block;
            text-decoration: none;
            padding: 14px;
            margin-bottom: 15px;
            border-radius: 12px;
            font-weight: 600;
            transition: 0.2s ease;
        }

        .btn-primary {
            background: #ff4d8d;
            color: #ffffff;
        }

        .btn-primary:hover {
            background: #e13c77;
            transform: translateY(-2px);
        }

        .btn-secondary {
            background: #1f1f1f;
            color: #dddddd;
            border: 1px solid #2f2f2f;
        }

        .btn-secondary:hover {
            background: #2a2a2a;
            color: #ffffff;
        }

        .footer {
            margin-top: 25px;
            font-size: 12px;
            color: #777777;
        }

        .badge {
            display: inline-block;
            margin-top: 10px;
            padding: 6px 12px;
            border-radius: 20px;
            background: rgba(255,77,141,0.15);
            color: #ff4d8d;
            font-size: 12px;
            font-weight: 600;
        }
    </style>
</head>

<body>
    <div class="container">
        <h1>📚 Library API</h1>
        <div class="subtitle">
            JSON & XML · JWT Auth · Flask · MySQL
        </div>

        <span class="badge">Dark Mode Enabled</span>

        <br><br>

        <a href="/login" class="btn btn-primary">🔐 Login</a>
        <a href="/register" class="btn btn-secondary">📝 Register</a>

        <div class="footer">
            Secure REST API with browser CRUD support
        </div>
    </div>
</body>
</html>
"""


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
