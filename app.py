import os
import pg8000.native
from flask import Flask, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "appdb")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

def get_connection():
    return pg8000.native.Connection(
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        host=DB_HOST,
        port=DB_PORT,
    )

@app.route("/health")
def health():
    return jsonify(status="ok"), 200

@app.route("/")
def index():
    try:
        conn = get_connection()
        result = conn.run("SELECT COUNT(*) FROM visits")
        conn.close()
        return jsonify(message="Stack is running", visit_rows=result[0][0]), 200
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
