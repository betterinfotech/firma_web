from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timezone, timedelta
from app.config import SECRET_KEY, VALID_DEVICES
from app.models.token_log import log_token_attempt
from app.services.telemetry import track_success

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
        track_success()
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
