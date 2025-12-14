# 📚 Library API (Flask + MySQL)

A **CRUD REST API with browser-based interface** built using **Flask**, **MySQL**, **JWT Authentication**, and **Session handling**.
This project supports **JSON and XML responses**, secure authentication, and full **Create, Read, Update, Delete** operations for books and authors.

---

## 📌 Project Overview

This project was developed as a **Final Project for CSE1**.
It demonstrates how to:

* Build a RESTful API using Flask
* Secure endpoints using JWT authentication
* Use MySQL for persistent storage
* Implement CRUD operations
* Support JSON and XML output formats
* Provide a browser-based UI for testing

---

## 🛠 Technologies Used

* **Python 3**
* **Flask**
* **MySQL**
* **JWT (JSON Web Token)**
* **Flask-Bcrypt**
* **HTML & CSS (Embedded Templates)**

---

## 🗂 Database Structure

### `users` table

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    password VARCHAR(255)
);
```

### `authors` table

```sql
CREATE TABLE authors (
    author_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100)
);
```

### `books` table

```sql
CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    author_id INT,
    genre VARCHAR(100),
    publish_year INT,
    available_copies INT,
    date_added DATE,
    FOREIGN KEY (author_id) REFERENCES authors(author_id)
);
```

---

## 🔐 Authentication Flow (JWT + Session)

1. User registers an account
2. User logs in using username and password
3. Server generates a JWT token
4. Token is stored in Flask session
5. Protected routes require a valid token

---

## 🚀 How to Run the Project

### 1️⃣ Install dependencies

```bash
pip install flask flask-bcrypt mysql-connector-python pyjwt
```

### 2️⃣ Configure MySQL

Update database credentials in `app.py`:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "library_db"
}
```

### 3️⃣ Create database

```sql
CREATE DATABASE library_db;
```

### 4️⃣ Run the application

```bash
python app.py
```

The server will start at:

```
http://127.0.0.1:5000
```

---

## 📚 API Endpoints

### 🔑 Authentication

| Method   | Endpoint    | Description            |
| -------- | ----------- | ---------------------- |
| GET/POST | `/register` | Register user          |
| GET/POST | `/login`    | Login and generate JWT |

---

### 📘 Books

| Method   | Endpoint             | Description    |
| -------- | -------------------- | -------------- |
| GET      | `/books`             | View all books |
| GET      | `/books/search?q=`   | Search books   |
| GET/POST | `/books/add`         | Add new book   |
| GET/POST | `/books/edit/<id>`   | Edit book      |
| GET      | `/books/delete/<id>` | Delete book    |

---

### ✍️ Authors

| Method   | Endpoint       | Description  |
| -------- | -------------- | ------------ |
| GET      | `/authors`     | View authors |
| GET/POST | `/authors/add` | Add author   |

---

## 🔄 JSON and XML Output

The API supports **JSON** and **XML** formats.

### Example JSON

```
GET /books?format=json
```

### Example XML

```
GET /books?format=xml
```

---

## 🧪 Example API Response (JSON)

```json
[
  {
    "book_id": 1,
    "title": "Python Basics",
    "author": "John Doe",
    "genre": "Programming",
    "publish_year": 2023,
    "available_copies": 5
  }
]
```

---

## 🧠 Features Implemented

* ✅ User Authentication (JWT + Session)
* ✅ CRUD operations
* ✅ Search functionality
* ✅ JSON & XML response handling
* ✅ Secure password hashing
* ✅ Browser-based UI
* ✅ Dark mode UI

---

## ⚠ Common Errors & Fixes

### ❌ `Unknown column 'date_added'`

**Fix:**

```sql
ALTER TABLE books ADD COLUMN date_added DATE;
```

### ❌ Buttons not working

**Fix:** Use `redirect(url_for("books"))` instead of returning plain HTML.

---

## 📄 Project Explanation Summary

This project demonstrates a complete RESTful API using Flask and MySQL with authentication and multiple response formats. It follows best practices such as password hashing, token-based security, and database normalization.

---

## 👨‍💻 Author

**Name:** Lee Neth
**Course:** CSE1
**Project:** Final Project – Library API

---

## ✅ Conclusion

The Library API successfully implements secure CRUD operations with real-world backend concepts, making it a strong foundation for learning RESTful API development using Flask.


