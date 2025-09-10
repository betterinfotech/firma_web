from datetime import datetime, timezone
import os
import psycopg2
from app.config import DB_CONFIG


def _connect():
    url = os.getenv("DATABASE_URL")
    if url:
        # leverage the same URL you already use for migrations; keep SSL
        return psycopg2.connect(url, sslmode="require")
    # fallback to old style (ensure DB_CONFIG has host/port/etc if you use this path)
    return psycopg2.connect(**DB_CONFIG)


def log_token_attempt(success: bool):
    try:
        conn = _connect()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO token_log (timestamp, success) VALUES (%s, %s)",
                (datetime.now(timezone.utc), success),
            )
            conn.commit()
        conn.close()
    except Exception as e:
        print("Log insert failed:", e)
