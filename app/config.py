import os
from dotenv import load_dotenv

load_dotenv()  # Automatically reads from .env file

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_dev_key")
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT", "5432"),
}
DATADOG_OPTIONS = {
    "statsd_host": os.getenv("STATSD_HOST", "127.0.0.1"),
    "statsd_port": int(os.getenv("STATSD_PORT", "8125")),
}
VALID_DEVICES = {"LAPTOP-S2QSIFSL": "Lenovo", "SOME_LOR_PC": "SOME_LOR_USER"}
