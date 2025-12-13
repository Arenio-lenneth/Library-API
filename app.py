from flask import Flask, request, jsonify, render_template_string
from flask_bcrypt import Bcrypt
from functools import wraps
import datetime
import jwt
import mysql.connector

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
CREATE TABLE IF NOT EXISTS books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    author VARCHAR(255),
    genre VARCHAR(100),
    publish_year INT,
    isbn VARCHAR(50),
    available_copies INT,
    date_added DATE
)
""")
db.commit()

# ==================================================
# SEED BOOKS
# ==================================================
def seed_books():
    cursor.execute("SELECT COUNT(*) AS total FROM books")
    if cursor.fetchone()["total"] > 0:
        return

    books = [
        ("1984","George Orwell","Dystopian",1949,"9780451524935",3),
        ("The Hobbit","J.R.R. Tolkien","Fantasy",1937,"9780547928227",4),
        ("Harry Potter","J.K. Rowling","Fantasy",1997,"9780590353427",10),
        ("The Alchemist","Paulo Coelho","Fiction",1988,"9780061122415",4)
    ]

    for b in books:
        cursor.execute("""
        INSERT INTO books
        (title,author,genre,publish_year,isbn,available_copies,date_added)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (*b, datetime.date.today()))
    db.commit()

# ==================================================
# JWT DECORATOR
# ==================================================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            jwt.decode(
                token.replace("Bearer ", ""),
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
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}

    cursor.execute("SELECT * FROM users WHERE username=%s", (data["username"],))
    if cursor.fetchone():
        return jsonify({"error": "User already exists"}), 409

    pw = bcrypt.generate_password_hash(data["password"]).decode()
    cursor.execute(
        "INSERT INTO users (username,password) VALUES (%s,%s)",
        (data["username"], pw)
    )
    db.commit()

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


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}

    cursor.execute("SELECT * FROM users WHERE username=%s", (data["username"],))
    user = cursor.fetchone()

    if not user or not bcrypt.check_password_hash(
            user["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {
            "user": data["username"],
            "exp": datetime.datetime.utcnow()
                   + datetime.timedelta(hours=2)
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    return jsonify({"token": token})

# ==================================================
# BOOKS API (FULL CRUD)
# ==================================================
@app.route("/api/books", methods=["GET", "POST"])
@token_required
def get_books():
    cursor.execute("SELECT * FROM books")
    return jsonify(cursor.fetchall())


@app.route("/api/books/<int:id>", methods=["GET", "PUT"])
@token_required
def get_book(id):
    cursor.execute("SELECT * FROM books WHERE book_id=%s", (id,))
    book = cursor.fetchone()
    if not book:
        return jsonify({"error": "Not found"}), 404
    return jsonify(book)


@app.route("/api/books", methods=["POST"])
@token_required
def add_book():
    data = request.get_json()
    cursor.execute("""
        INSERT INTO books
        (title,author,genre,publish_year,isbn,available_copies,date_added)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["title"], data["author"], data["genre"],
        data["publish_year"], data["isbn"],
        data["available_copies"],
        datetime.date.today()
    ))
    db.commit()
    return jsonify({"message": "Book added"}), 201


@app.route("/api/books/<int:id>", methods=["PUT"])
@token_required
def update_book(id):
    data = request.get_json()
    cursor.execute("""
        UPDATE books
        SET title=%s, author=%s, genre=%s, available_copies=%s
        WHERE book_id=%s
    """, (
        data["title"], data["author"],
        data["genre"], data["available_copies"], id
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
