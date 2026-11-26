"""Cached profile info so lookups survive Instagram rate limits."""

import json
import os

from .config import profile_cache_path

PROFILE_FIELDS = (
    "username", "full_name", "biography", "external_url", "posts",
    "followers", "following", "userid", "is_private", "is_verified",
    "fetched_at",
)


def load_profile(username):
    """Return cached basic info marked as cached, or None."""
    path = profile_cache_path(username)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        if not isinstance(data, dict) or any(key not in data for key in PROFILE_FIELDS):
            return None
        data['cached'] = True
        return data
    except Exception:
        return None


def save_profile(username, info):
    path = profile_cache_path(username)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, 'w') as f:
            json.dump(info, f)
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
