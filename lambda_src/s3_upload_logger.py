# s3_upload_logger.py
from __future__ import annotations
import os
from datetime import datetime, timezone
from urllib.parse import unquote_plus
import psycopg2  # keep psycopg2 if that's already in requirements


def _dsn_from_env() -> str:
    # Prefer DATABASE_URL if present; else build from PG_* vars
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]  # e.g. postgresql://... ?sslmode=require
    return (
        f"host={os.environ['PG_HOST']} "
        f"port={os.environ.get('PG_PORT','5432')} "
        f"dbname={os.environ['PG_DB']} "
        f"user={os.environ['PG_USER']} "
        f"password={os.environ['PG_PASSWORD']} "
        f"sslmode=require"
    )


def _conn():
    return psycopg2.connect(_dsn_from_env(), connect_timeout=5)


def insert_one(file_key: str) -> None:
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.file_upload_log (upload_time, file_name)
                VALUES (NOW(), %s)
                ON CONFLICT DO NOTHING
                """,
                (file_key,),
            )


# Keep Lambda-style handler usable if you later wire S3 events
def handler(event, context):
    records = event.get("Records", [])
    if not records:
        return {"ok": True, "inserted": 0}
    inserted = 0
    with _conn() as conn:
        with conn.cursor() as cur:
            now_utc = datetime.now(timezone.utc)
            for r in records:
                key_enc = r["s3"]["object"]["key"]
                key = unquote_plus(key_enc)
                cur.execute(
                    "INSERT INTO public.file_upload_log (upload_time, file_name) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (now_utc, key),
                )
                inserted += 1
    return {"ok": True, "inserted": inserted}
