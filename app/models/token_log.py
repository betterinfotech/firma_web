from datetime import datetime, timezone
import psycopg2
from app.config import DB_CONFIG


def log_token_attempt(success: bool):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO token_log (timestamp, success) VALUES (%s, %s)",
                (datetime.now(timezone.utc), success),
            )
            conn.commit()
        conn.close()
    except Exception as e:
        print("Log insert failed:", e)
