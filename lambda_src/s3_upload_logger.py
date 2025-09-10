from __future__ import annotations
import os
from datetime import datetime, timezone
import psycopg2
from urllib.parse import unquote_plus


def _conn():
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        port=os.environ.get("PG_PORT", "5432"),
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        connect_timeout=5,
        sslmode="require",
    )


def handler(event, context):
    # S3 may batch multiple records
    records = event.get("Records", [])
    if not records:
        return {"ok": True, "inserted": 0}

    inserted = 0
    conn = None
    try:
        conn = _conn()
        with conn.cursor() as cur:
            now_utc = datetime.now(timezone.utc)
            for r in records:
                key_enc = r["s3"]["object"]["key"]
                key = unquote_plus(
                    key_enc
                )  # decode URL-encoded keys like "foo%20bar.txt"
                cur.execute(
                    "INSERT INTO file_upload_log (upload_time, file_name) VALUES (%s, %s)",
                    (now_utc, key),
                )
                inserted += 1
        conn.commit()
        return {"ok": True, "inserted": inserted}
    finally:
        if conn:
            conn.close()
