import requests

BASE = "http://127.0.0.1:5000"

# -----------------------------
# REGISTER (API)
# -----------------------------
register_response = requests.post(
    f"{BASE}/api/register",
    json={"username": "admin", "password": "admin123"}
)

print("REGISTER STATUS:", register_response.status_code)
print("REGISTER RESPONSE:", register_response.text)

# -----------------------------
# LOGIN (API)
# -----------------------------
login_response = requests.post(
    f"{BASE}/api/login",
    json={"username": "admin", "password": "admin123"}
)

print("\nLOGIN STATUS:", login_response.status_code)
print("RAW RESPONSE:", login_response.text)

if login_response.status_code != 200:
    print("❌ LOGIN FAILED")
    exit()

token = login_response.json()["token"]
print("✅ TOKEN:", token)

headers = {
    "Authorization": f"Bearer {token}"
}

# -----------------------------
# GET BOOKS (API)
# -----------------------------
books = requests.get(f"{BASE}/api/books", headers=headers)
print("\nBOOKS STATUS:", books.status_code)
print("BOOKS RESPONSE:", books.json())

# -----------------------------
# ADD A BOOK (API)
# -----------------------------
add_book = requests.post(
    f"{BASE}/api/books",
    json={
        "title": "Test Book",
        "author": "Test Author",
        "genre": "Fiction",
        "publish_year": 2023,
        "isbn": "1234567890",
        "available_copies": 5
    },
    headers=headers
)

print("\nADD BOOK STATUS:", add_book.status_code)
print("ADD BOOK RESPONSE:", add_book.text)

# -----------------------------
# SEARCH BOOKS (API)
# -----------------------------
search = requests.get(
    f"{BASE}/api/search?q=Fiction",
    headers=headers
)

print("\nSEARCH STATUS:", search.status_code)
print("SEARCH RESPONSE:", search.json())
