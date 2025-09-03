import os
from typing import Dict

"""
This module handles configuration settings for the application and allows them to be easily imported.
"""
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

VALID_DEVICES = {"LAPTOP-S2QSIFSL": "Lenovo", "SOME_LOR_PC": "SOME_LOR_USER"}

AWS_REGION = os.getenv("AWS_REGION", "us-east-2")
S3_BUCKET = os.getenv("S3_BUCKET", "firma-bim-prod")
