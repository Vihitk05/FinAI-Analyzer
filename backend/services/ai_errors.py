class LLMError(Exception):
    pass


class TransientLLMError(LLMError):
    pass


class QuotaExhaustedError(LLMError):
    pass


class LLMTimeoutError(LLMError):
    pass


QUOTA_EXHAUSTED_MESSAGE = (
    "The free AI model quota for today is exhausted. Add your own OpenRouter API key "
    "(LLM_API_KEY) or try again after the daily reset."
)


def is_daily_quota_exhausted(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(
        term in message
        for term in ("free-models-per-day", "free_tier_daily", "openrouter_free_tier_daily", "free-model daily")
    )


def is_transient(exc: Exception) -> bool:
    message = str(exc).lower()
    if is_daily_quota_exhausted(exc):
        return False
    return any(term in message for term in ("rate limit", "rate-limit", "429", "timeout", "503", "502", "connection"))
