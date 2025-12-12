import requests

BASE = "http://127.0.0.1:5000"

def test_get_books():
    r = requests.get(BASE + "/books")
    assert r.status_code == 200

def test_search():
    r = requests.get(BASE + "/search?q=Harry")
    assert r.status_code == 200
