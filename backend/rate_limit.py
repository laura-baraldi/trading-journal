from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_rate_limit_key(request: Request):
    # Use the authenticated user ID when available; otherwise fall back to the client IP.
    user_id = getattr(request.state, "user_id", None)

    if user_id:
        # SlowAPI uses string keys to identify each rate-limit bucket.
        return str(user_id)

    return get_remote_address(request)


limiter = Limiter(key_func=get_rate_limit_key)
