import os

from dotenv import load_dotenv

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))


class ConfigError(RuntimeError):
    pass


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://finai:finai@localhost:5433/finai")

LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")


LLM_PRIMARY_MODEL = os.environ.get("LLM_PRIMARY_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
LLM_REASONING_MODEL = os.environ.get("LLM_REASONING_MODEL", "z-ai/glm-5.2:free")
LLM_FAST_MODEL = os.environ.get("LLM_FAST_MODEL", "google/gemma-4-26b-a4b-it:free")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
FLASK_ENV = os.environ.get("FLASK_ENV", "development")
IS_PRODUCTION = FLASK_ENV == "production"

CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
if os.environ.get("FRONTEND_ORIGIN"):
    CORS_ORIGINS = list(dict.fromkeys(CORS_ORIGINS + [os.environ["FRONTEND_ORIGIN"].strip()]))

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

ALLOWED_UPLOAD_EXTENSIONS = {".pdf"}

EMBEDDING_MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")

EMBEDDING_DOCUMENT_MAX_CHARS = int(os.environ.get("EMBEDDING_DOCUMENT_MAX_CHARS", "400"))


AUTH_SECRET = os.environ.get("AUTH_SECRET")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = int(os.environ.get("JWT_EXPIRY_DAYS", "7"))
AUTH_COOKIE_NAME = "finai_session"
AUTH_COOKIE_SECURE = IS_PRODUCTION
AUTH_COOKIE_SAMESITE = "None" if IS_PRODUCTION else "Lax"


JOB_POLL_INTERVAL_SECONDS = float(os.environ.get("JOB_POLL_INTERVAL_SECONDS", "2"))
JOB_STALE_AFTER_SECONDS = int(os.environ.get("JOB_STALE_AFTER_SECONDS", "300"))
JOB_MAX_RETRIES = int(os.environ.get("JOB_MAX_RETRIES", "3"))
JOB_OCR_TIMEOUT_SECONDS = int(os.environ.get("JOB_OCR_TIMEOUT_SECONDS", "900"))
DISABLE_BACKGROUND_WORKER = os.environ.get("DISABLE_BACKGROUND_WORKER", "").lower() in {"1", "true", "yes"}

MAX_QUERY_LENGTH = int(os.environ.get("MAX_QUERY_LENGTH", "2000"))


def validate_required_config():
    missing = []
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    if not AUTH_SECRET:
        missing.append("AUTH_SECRET")
    if missing:
        raise ConfigError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Copy backend/.env.example to backend/.env and fill them in."
        )
