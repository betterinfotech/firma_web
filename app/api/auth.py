from flask import Blueprint, request, jsonify, current_app
import jwt
from datetime import datetime, timezone, timedelta
from app.config import SECRET_KEY, VALID_DEVICES, S3_BUCKET, AWS_REGION
from app.models.token_log import log_token_attempt
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from werkzeug.datastructures import FileStorage
from lambda_src.s3_upload_logger import insert_one


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    return jsonify({"message": "Auth server is running."})


@auth_bp.route("/get-token", methods=["POST"])
def get_token():
    data = request.get_json()
    if not data:
        log_token_attempt(False)
        return jsonify({"error": "Missing JSON body"}), 400

    device_id = data.get("device_id")
    auth_user = data.get("auth_user")
    if not device_id or not auth_user:
        log_token_attempt(False)
        return jsonify({"error": "Missing credentials"}), 400

    expected_user = VALID_DEVICES.get(device_id)
    if expected_user and expected_user == auth_user:
        log_token_attempt(True)
        payload = {
            "device_id": device_id,
            "auth_user": auth_user,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({"token": token})
    else:
        log_token_attempt(False)
        return jsonify({"error": "Unauthorized"}), 401


@auth_bp.route("/verify-token", methods=["POST"])
def verify_token():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return jsonify({"error": "Missing token"}), 401
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"valid": True, "payload": payload})
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token"}), 401


@auth_bp.route("/secure-data")
def secure_data():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify(
            {"message": f"Hello, {decoded['auth_user']} from {decoded['device_id']}"}
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401


@auth_bp.route("/upload", methods=["POST"])
def upload_file():
    """
    Accepts multipart/form-data with field 'file'.
    Requires a valid Bearer JWT in the Authorization header.
    Streams file directly to S3.
    """
    # ---- Require JWT ----
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # ---- File upload ----
    if not S3_BUCKET:
        return jsonify(ok=False, error="S3 bucket not configured"), 500

    file: FileStorage | None = request.files.get("file")
    if file is None or file.filename == "":
        return jsonify(ok=False, error="No file provided (field 'file')"), 400

    key = f"uploads/{file.filename}"
    s3 = boto3.client("s3", region_name=AWS_REGION)

    try:
        s3.upload_fileobj(
            file.stream,
            S3_BUCKET,
            key,
            ExtraArgs={
                "ContentType": file.mimetype or "application/octet-stream",
                "ServerSideEncryption": "AES256",
            },
        )

        # Now log to DB
        try:
            insert_one(key)  # e.g. "uploads/foo.txt"
            current_app.logger.info("Logged upload %s", key)
        except Exception:
            current_app.logger.exception("Failed logging upload for %s", key)

    except (ClientError, BotoCoreError) as e:
        return jsonify(ok=False, error=f"S3 upload failed: {str(e)}"), 502

    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=900
    )

    return jsonify(ok=True, bucket=S3_BUCKET, key=key, presigned_get=url), 201


@auth_bp.route("/files/<path:filename>", methods=["GET"])
def check_file_exists(filename: str):
    """
    RESTful endpoint to check if a file exists in S3.
    Requires:
      - Authorization: Bearer <token>
      - Path parameter: /files/<filename>
    Returns JSON: { exists: true/false }
    """
    # ---- Require JWT ----
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid token"}), 401

    token = auth_header.split(" ")[1]
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # ---- Check S3 ----
    s3 = boto3.client("s3", region_name=AWS_REGION)
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=f"uploads/{filename}")
        return jsonify(exists=True)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("404", "NotFound", "NoSuchKey"):
            return jsonify(exists=False)
        return jsonify(error=str(e)), 502
