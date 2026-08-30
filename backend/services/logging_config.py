import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "extra_fields", {}).items():
            payload[key] = value
        return json.dumps(payload)


def configure_logging(level="INFO"):
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    if level != "DEBUG":
        for noisy in (
            "werkzeug", "psycopg", "psycopg.pool", "urllib3",
            "httpx", "httpcore", "openai", "fastembed",
        ):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name):
    return logging.getLogger(name)


def log_extra(**fields):
    return {"extra_fields": fields}
