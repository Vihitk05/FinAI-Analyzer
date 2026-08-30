from functools import wraps

from flask import g, jsonify, request

import config
from services import auth as auth_service
from services import db


def get_current_user_id() -> int | None:
    token = request.cookies.get(config.AUTH_COOKIE_NAME)
    return auth_service.decode_session_token(token)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({"error": "Authentication required"}), 401

        user = db.get_user_by_id(user_id)
        if user is None:
            return jsonify({"error": "Authentication required"}), 401

        g.user_id = user_id
        g.user = user
        return view(*args, **kwargs)

    return wrapped


def set_auth_cookie(response, token: str):
    response.set_cookie(
        config.AUTH_COOKIE_NAME,
        token,
        httponly=True,
        secure=config.AUTH_COOKIE_SECURE,
        samesite=config.AUTH_COOKIE_SAMESITE,
        max_age=config.JWT_EXPIRY_DAYS * 24 * 60 * 60,
        path="/",
    )


def clear_auth_cookie(response):
    response.delete_cookie(
        config.AUTH_COOKIE_NAME,
        httponly=True,
        secure=config.AUTH_COOKIE_SECURE,
        samesite=config.AUTH_COOKIE_SAMESITE,
        path="/",
    )
