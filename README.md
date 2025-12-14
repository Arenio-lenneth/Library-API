## 🔐 JWT Authentication

The application uses JWT to secure API endpoints.

```python
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization") or session.get("token")
        if not token:
            return jsonify({"error": "Token missing"}), 401
        jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return f(*args, **kwargs)
    return decorated

