from flask import Flask, request, jsonify, render_template_string
from flask_bcrypt import Bcrypt
from functools import wraps
import datetime
import jwt
import mysql.connector
from flask import session

def to_xml(data, root_name="items"):
    from xml.etree.ElementTree import Element, SubElement, tostring

    root = Element(root_name)

    for item in data:
        item_el = SubElement(root, "item")
        for key, value in item.items():
            child = SubElement(item_el, key)
            child.text = str(value)

    return tostring(root, encoding="utf-8")


# ==================================================
# APP SETUP
# ==================================================
app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config["SECRET_KEY"] = "supersecretkey"
app.config["JWT_EXP_HOURS"] = 2

# ==================================================
# DATABASE (MySQL)
# ==================================================
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",       
    "database": "library_db"
}

db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor(dictionary=True)

# ==================================================
# TABLES
# ==================================================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    password VARCHAR(255)
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS authors (
    author_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    author_id INT,
    genre VARCHAR(100),
    publish_year INT,
    isbn VARCHAR(50),
    available_copies INT,
    date_added DATE,
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
)
""")
db.commit()

# ==================================================
# SEED AUTHORS AND BOOKS
# ==================================================
def seed_authors():
    authors = [
        "J.K.", "Rowling",
        "George", "Orwell",
        "Harper", "Lee",
        "F. Scott", "Fitzgerald",
        "J.D.", "Salinger",
        "Jane", "Austen",
        "J.R.R.", "Tolkien",
        "Paulo", "Coelho",
        "Dan", "Brown",
        "Suzanne", "Collins"
    ]

    for first_name, last_name in zip(authors[::2], authors[1::2]):
        cursor.execute(
            "INSERT IGNORE INTO authors (first_name, last_name) VALUES (%s, %s)",
            (first_name, last_name)
        )
    db.commit()


def seed_books():
    cursor.execute("SELECT COUNT(*) AS total FROM books")
    if cursor.fetchone()["total"] > 0:
        return

    books = [
        ("Harry Potter and the Chamber of Secrets", 1, "Fantasy", 1998, "9780439064873", 4),
        ("1984", 2, "Dystopian", 1949, "9780451524935", 3),
        ("The Hobbit", 7, "Fantasy", 1937, "9780547928227", 6),
    ]

    for b in books:
        cursor.execute("""
        INSERT INTO books
        (title, author_id, genre, publish_year, isbn, available_copies, date_added)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (*b, datetime.date.today()))

    db.commit()


seed_authors()
seed_books()


# ==================================================
# JWT DECORATOR
# ==================================================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        # 1️⃣ API token
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.replace("Bearer ", "")

        # 2️⃣ Browser session token
        if not token:
            token = session.get("token")

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            jwt.decode(
                token,
                app.config["SECRET_KEY"],
                algorithms=["HS256"]
            )
        except:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)

    return decorated


# ==================================================
# AUTH API
# ==================================================
@app.route("/api/register", methods=["GET", "POST"])
def api_register():
    # ===============================
    # GET → Show HTML form (Browser)
    # ===============================
    if request.method == "GET":
        return """
        <h1>Register (API)</h1>
        <form method="POST">
            <input name="username" placeholder="Username" required><br><br>
            <input name="password" type="password" placeholder="Password" required><br><br>
            <button>Register</button>
        </form>
        <br>
        <a href="/login">Login</a>
        """

    # ===============================
    # POST → JSON or Form
    # ===============================
    data = request.get_json(silent=True)

    if data:
        username = data.get("username")
        password = data.get("password")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return jsonify({"error": "User already exists"}), 409

    pw = bcrypt.generate_password_hash(password).decode()
    cursor.execute(
        "INSERT INTO users (username,password) VALUES (%s,%s)",
        (username, pw)
    )
    db.commit()

    # Browser-friendly response
    if not data:
        return """
        <h2>Registration successful</h2>
        <a href="/login">Go to Login</a>
        """

    # API response
    return jsonify({"message": "Registered successfully"}), 201


@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return """
        <h1>Register</h1>
        <form method="POST">
            <input name="username" placeholder="Username" required><br><br>
            <input name="password" type="password" placeholder="Password" required><br><br>
            <button>Register</button>
        </form>
        <br>
        <a href="/login">Already have an account? Login</a>
        """

    username = request.form["username"]
    password = request.form["password"]

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return "<h3>User already exists</h3><a href='/register'>Back</a>"

    pw = bcrypt.generate_password_hash(password).decode()

    cursor.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s)",
        (username, pw)
    )
    db.commit()

    return """
    <h2>Registration successful</h2>
    <a href="/login">Go to Login</a>
    """


@app.route("/api/login", methods=["GET", "POST"])
def api_login():
    if request.method == "GET":
        return """
        <h1>API Login</h1>
        <form method="POST">
            <input name="username" placeholder="Username" required><br><br>
            <input name="password" type="password" required><br><br>
            <button>Login</button>
        </form>
        """

    # Accept JSON or FORM
    if request.is_json:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return "<h3>Invalid credentials</h3>"

    token = jwt.encode(
        {
            "user": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    # 🔐 Store token in browser session
    session["token"] = token

    # If browser → redirect
    if not request.is_json:
        return f"""
        <h2>Login Success</h2>
        <p>JWT saved in session</p>
        <a href="/api/books">View Books</a>
        """

    return jsonify({"token": token})


# ==================================================
# BOOKS API (FULL CRUD)
# ==================================================
@app.route("/api/books", methods=["GET"])
@token_required
def api_books():
    cursor.execute("""
        SELECT 
            b.book_id,
            b.title,
            CONCAT(a.first_name, ' ', a.last_name) AS author,
            b.genre,
            b.publish_year,
            b.isbn,
            b.available_copies
        FROM books b
        JOIN authors a ON b.author_id = a.author_id
    """)
    books = cursor.fetchall()

    format_type = request.args.get("format", "json").lower()

    if format_type == "xml":
        xml_data = to_xml(books, root_name="books")
        return app.response_class(xml_data, mimetype="application/xml")

    return jsonify(books)


@app.route("/api/authors", methods=["GET"])
@token_required
def get_authors():
    cursor.execute("SELECT * FROM authors")
    authors = cursor.fetchall()

    # Browser
    if "text/html" in request.headers.get("Accept", ""):
        html = """
        <h1>Authors</h1>
        {% for a in authors %}
        <p>{{a.author_id}} - {{a.name}}</p>
        {% endfor %}
        """
        return render_template_string(html, authors=authors)

    return jsonify(authors)


@app.route("/api/books", methods=["POST"])
@token_required
def add_book():
    data = request.get_json()
    cursor.execute("""
        INSERT INTO books
        (title, author_id, genre, publish_year, isbn, available_copies, date_added)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["title"],
        data["author_id"],
        data["genre"],
        data["publish_year"],
        data["isbn"],
        data["available_copies"],
        datetime.date.today()
    ))
    db.commit()
    return jsonify({"message": "Book added"}), 201


@app.route("/api/authors", methods=["POST"])
@token_required
def add_author():
    data = request.get_json()
    cursor.execute(
        "INSERT INTO authors (first_name, last_name) VALUES (%s, %s)",
        (data["first_name"], data["last_name"])
    )
    db.commit()
    return jsonify({"message": "Author added"}), 201



@app.route("/api/books/<int:id>", methods=["PUT"])
@token_required
def update_book(id):
    data = request.get_json()
    cursor.execute("""
        UPDATE books
        SET title=%s, author_id=%s, genre=%s, available_copies=%s
        WHERE book_id=%s
    """, (
        data["title"],
        data["author_id"],
        data["genre"],
        data["available_copies"],
        id
    ))
    db.commit()
    return jsonify({"message": "Book updated"})



@app.route("/api/books/<int:id>", methods=["DELETE"])
@token_required
def delete_book(id):
    cursor.execute("DELETE FROM books WHERE book_id=%s", (id,))
    db.commit()
    return jsonify({"message": "Book deleted"})

# ==================================================
# WEB (HTML)
# ==================================================
@app.route("/")
def index():
    return """
    <h2>Library API Running (MySQL)</h2>
    <a href="/login">Login</a><br><br>
    <a href="/register">Register</a>
    """



@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return """
        <h1>Login</h1>
        <form method="POST">
        <input name="username" required>
        <input name="password" type="password" required>
        <button>Login</button>
        </form>
        """

    cursor.execute("SELECT * FROM users WHERE username=%s",
                   (request.form["username"],))
    user = cursor.fetchone()

    if not user or not bcrypt.check_password_hash(
            user["password"], request.form["password"]):
        return "<h3>Invalid credentials</h3>"

    token = jwt.encode(
        {
            "user": request.form["username"],
            "exp": datetime.datetime.utcnow()
                   + datetime.timedelta(hours=2)
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return f"""
    <h2>Login Success</h2>
    <textarea rows=6 cols=80>{token}</textarea>
    <br><a href="/books">View Books</a>
    """


@app.route("/books")
def books_page():
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    html = """
    <h1>Library Books</h1>
    {% for b in books %}
    <pre>
ID: {{b.book_id}}
Title: {{b.title}}
Author: {{b.author}}
Genre: {{b.genre}}
Year: {{b.publish_year}}
    </pre>
    {% endfor %}
    """
    return render_template_string(html, books=books)

# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    seed_books()
    app.run(debug=True)
