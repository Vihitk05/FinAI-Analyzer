from flask import Blueprint, g, jsonify, request

from services import auth as auth_service
from services import db
from services.logging_config import get_logger, log_extra
from utils.auth_utils import clear_auth_cookie, login_required, set_auth_cookie

logger = get_logger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    payload = request.get_json(silent=True) or {}

    try:
        name, email = auth_service.validate_signup_input(
            payload.get("name", ""),
            payload.get("email", ""),
            payload.get("password", ""),
            payload.get("confirmPassword", ""),
        )
    except auth_service.AuthError as exc:
        return jsonify({"error": str(exc)}), 400

    if db.get_user_by_email(email) is not None:
        return jsonify({"error": "An account with this email already exists"}), 409

    password_hash = auth_service.hash_password(payload.get("password", ""))
    try:
        user = db.create_user(name, email, password_hash)
    except db.DatabaseError as exc:
        return jsonify({"error": str(exc)}), 409

    logger.info("user_signed_up", extra=log_extra(user_id=user["id"]))
    token = auth_service.create_session_token(user["id"])
    response = jsonify({"user": auth_service.public_user(user)})
    set_auth_cookie(response, token)
    return response, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    email = auth_service.normalize_email(payload.get("email", ""))
    password = payload.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.get_user_by_email(email)
    if user is None or not auth_service.verify_password(password, user["password_hash"]):
        logger.info("login_failed", extra=log_extra(email=email))
        return jsonify({"error": "Invalid email or password"}), 401

    logger.info("login_succeeded", extra=log_extra(user_id=user["id"]))
    token = auth_service.create_session_token(user["id"])
    response = jsonify({"user": auth_service.public_user(user)})
    set_auth_cookie(response, token)
    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"success": True})
    clear_auth_cookie(response)
    return response


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify({"user": auth_service.public_user(g.user)})
