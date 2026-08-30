import datetime
import re

import bcrypt
import jwt

from config import AUTH_SECRET, JWT_ALGORITHM, JWT_EXPIRY_DAYS

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MIN_PASSWORD_LENGTH = 8


class AuthError(Exception):
    pass


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_signup_input(name: str, email: str, password: str, confirm_password: str):
    name = (name or "").strip()
    email = normalize_email(email)

    if not name:
        raise AuthError("Name is required")
    if not email or not _EMAIL_RE.match(email):
        raise AuthError("A valid email address is required")
    if password != confirm_password:
        raise AuthError("Passwords do not match")

    problems = password_strength_issues(password)
    if problems:
        raise AuthError(problems[0])

    return name, email


def password_strength_issues(password: str) -> list[str]:
    password = password or ""
    issues = []
    if len(password) < _MIN_PASSWORD_LENGTH:
        issues.append(f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long")
    if not re.search(r"[A-Za-z]", password):
        issues.append("Password must contain at least one letter")
    if not re.search(r"[0-9]", password):
        issues.append("Password must contain at least one number")
    return issues


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_session_token(user_id: int) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + datetime.timedelta(days=JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, AUTH_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> int | None:

    if not token:
        return None
    try:
        payload = jwt.decode(token, AUTH_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        return None


def public_user(user: dict) -> dict:

    return {"id": user["id"], "name": user["name"], "email": user["email"]}
