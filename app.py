from flask import Flask, request, jsonify, make_response
import os
import importlib
mysql_connector = None
try:
    mysql_connector = importlib.import_module("mysql.connector")
    MYSQL_AVAILABLE = True
except Exception:
    MYSQL_AVAILABLE = False
import xmltodict
import jwt
import datetime
from functools import wraps
from flask_bcrypt import Bcrypt
from config import Config

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Load configuration from `config.py` (allows env overrides)
app.config.from_object(Config)

# Database connection using config values. If mysql-connector is not installed
# fall back to a local SQLite DB so the app can run for development/testing.
if MYSQL_AVAILABLE:
    try:
        db = mysql_connector.connect(
            host=app.config.get("MYSQL_HOST", "localhost"),
            user=app.config.get("MYSQL_USER", "root"),
            password=app.config.get("MYSQL_PASSWORD", ""),
            database=app.config.get("MYSQL_DB", "library_db")
        )
        cursor = db.cursor(dictionary=True)
    except mysql_connector.Error as e:
        raise RuntimeError(f"Database connection failed: {e}")
else:
    # Use SQLite fallback
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), "library.sqlite3")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    raw_cursor = conn.cursor()

    class SQLiteCursorWrapper:
        def execute(self, sql, params=None):
            if params is None:
                params = ()
            # convert MySQL-style %s placeholders to SQLite ? placeholders
            sql_conv = sql.replace("%s", "?")
            return raw_cursor.execute(sql_conv, params)

        def fetchone(self):
            row = raw_cursor.fetchone()
            return dict(row) if row is not None else None

        def fetchall(self):
            rows = raw_cursor.fetchall()
            return [dict(r) for r in rows]

    cursor = SQLiteCursorWrapper()
    db = conn

    # Ensure minimal tables exist for local testing
    raw_cursor.execute(
        """CREATE TABLE IF NOT EXISTS users (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           username TEXT UNIQUE NOT NULL,
           password TEXT NOT NULL
        )"""
    )
    raw_cursor.execute(
        """CREATE TABLE IF NOT EXISTS books (
           book_id INTEGER PRIMARY KEY AUTOINCREMENT,
           title TEXT,
           author_id INTEGER,
           genre TEXT,
           publish_year INTEGER,
           isbn TEXT,
           available_copies INTEGER
        )"""
    )
    conn.commit()


# ---------------------------------------------
# JWT AUTH DECORATOR
# ---------------------------------------------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Token must be included in the request headers
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].replace("Bearer ", "")

        if not token:
            return jsonify({"error": "Token missing"}), 401

        try:
            jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------
# REGISTER ENDPOINT (create user with bcrypt hash)
# ---------------------------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    if cursor.fetchone():
        return jsonify({"error": "User already exists"}), 409

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, pw_hash))
    db.commit()
    return jsonify({"message": "User created"}), 201


# ---------------------------------------------
# LOGIN ENDPOINT (returns JWT)
# ---------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"error": "Wrong password"}), 401

    token = jwt.encode(
        {
            "user": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=app.config.get("JWT_EXP_HOURS", 2))
        },
        app.config["SECRET_KEY"],
        algorithm="HS256"
    )

    # PyJWT v2 returns a string, older versions may return bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return jsonify({"token": token})


# ---------------------------------------------
# Helper for XML/JSON formatting
# ---------------------------------------------
def respond(data, format_type):
    if format_type == "xml":
        xml_data = xmltodict.unparse({"response": data}, pretty=True)
        response = make_response(xml_data, 200)
        response.headers["Content-Type"] = "application/xml"
        return response
    return jsonify(data)


# ---------------------------------------------
# PROTECTED ROUTES (ALL REQUIRE JWT)
# ---------------------------------------------

# GET ALL BOOKS
@app.route('/books', methods=['GET'])
@token_required
def get_books():
    format_type = request.args.get("format", "json")
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return respond(books, format_type)


# GET ONE BOOK
@app.route('/books/<int:id>', methods=['GET'])
@token_required
def get_book(id):
    cursor.execute("SELECT * FROM books WHERE book_id = %s", (id,))
    book = cursor.fetchone()
    if not book:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book)


# ADD BOOK
@app.route('/books', methods=['POST'])
@token_required
def add_book():
    data = request.json or {}
    required = ["title", "author_id", "genre", "publish_year", "isbn", "available_copies"]

    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    sql = """INSERT INTO books (title, author_id, genre, publish_year, isbn, available_copies)
             VALUES (%s, %s, %s, %s, %s, %s)"""
    values = (data["title"], data["author_id"], data["genre"], data["publish_year"],
              data["isbn"], data["available_copies"])

    cursor.execute(sql, values)
    db.commit()

    return jsonify({"message": "Book added"}), 201


# UPDATE BOOK
@app.route('/books/<int:id>', methods=['PUT'])
@token_required
def update_book(id):
    data = request.json or {}
    sql = """UPDATE books SET title=%s, genre=%s, publish_year=%s, 
             isbn=%s, available_copies=%s WHERE book_id=%s"""
    values = (data.get("title"), data.get("genre"), data.get("publish_year"),
              data.get("isbn"), data.get("available_copies"), id)

    cursor.execute(sql, values)
    db.commit()
    return jsonify({"message": "Book updated"})


# DELETE BOOK
@app.route('/books/<int:id>', methods=['DELETE'])
@token_required
def delete_book(id):
    cursor.execute("DELETE FROM books WHERE book_id=%s", (id,))
    db.commit()
    return jsonify({"message": "Book deleted"})


# SEARCH
@app.route('/search')
@token_required
def search_books():
    keyword = request.args.get("q", "")
    sql = "SELECT * FROM books WHERE title LIKE %s OR genre LIKE %s"
    cursor.execute(sql, (f"%{keyword}%", f"%{keyword}%"))
    results = cursor.fetchall()
    return jsonify(results)


@app.route('/')
def index():
    return jsonify({"message": "Library API is running"})


if __name__ == "__main__":
    app.run(debug=True)
