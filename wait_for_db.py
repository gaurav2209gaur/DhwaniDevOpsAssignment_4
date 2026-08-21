import os
import sys
import time
import pg8000.native

DB_HOST = os.environ.get("DB_HOST", "db")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "appdb")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

MAX_RETRIES = 30
DELAY_SECONDS = 2

def main():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = pg8000.native.Connection(
                user=DB_USER, password=DB_PASSWORD,
                database=DB_NAME, host=DB_HOST, port=DB_PORT,
            )
            conn.run("SELECT 1")
            conn.run("""
                CREATE TABLE IF NOT EXISTS visits (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            conn.run("INSERT INTO visits DEFAULT VALUES")
            conn.close()
            print(f"Database ready and seeded after {attempt} attempt(s)", flush=True)
            return 0
        except Exception as e:
            print(f"DB not ready (attempt {attempt}/{MAX_RETRIES}): {e}", flush=True)
            time.sleep(DELAY_SECONDS)
    print("Database never became ready — exiting", flush=True)
    return 1

if __name__ == "__main__":
    sys.exit(main())
