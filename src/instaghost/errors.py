"""instagrapi exceptions grouped by the recovery action they need."""

from instagrapi import exceptions as ig_exc

# Instagram throttled us: back off and retry later
RATE_LIMIT_ERRORS = (
    ig_exc.RateLimitError,
    ig_exc.PleaseWaitFewMinutes,
    ig_exc.ClientThrottledError,
    ig_exc.ClientConnectionError,
)

# The session is missing, expired, or not allowed to do this
LOGIN_ERRORS = (
    ig_exc.LoginRequired,
    ig_exc.ClientLoginRequired,
    ig_exc.ClientUnauthorizedError,
)
