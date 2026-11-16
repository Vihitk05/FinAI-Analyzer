from __future__ import annotations

import json
import os
import resource

from services.logging_config import get_logger, log_extra

logger = get_logger(__name__)


def _rss_mb() -> float | None:
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        with open("/proc/self/statm") as f:
            resident_pages = int(f.read().split()[1])
        return round(resident_pages * page_size / (1024 * 1024), 1)
    except Exception:
        try:
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if rss > 10_000_000:
                rss = rss / 1024
            return round(rss / 1024, 1)
        except Exception:
            return None


def log_memory(event: str, **fields) -> None:
    payload = {"event": event, "rss_mb": _rss_mb(), **fields}
    try:
        logger.info("[MEMORY] %s", json.dumps(payload, sort_keys=True), extra=log_extra(**payload))
    except Exception:
        return
