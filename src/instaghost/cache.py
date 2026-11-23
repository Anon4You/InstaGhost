"""Cached profile info so lookups survive Instagram rate limits."""

import json

from .config import profile_cache_path


def load_profile(username):
    """Return cached basic info marked as cached, or None."""
    path = profile_cache_path(username)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        data['cached'] = True
        return data
    except Exception:
        return None


def save_profile(username, info):
    try:
        with open(profile_cache_path(username), 'w') as f:
            json.dump(info, f)
    except Exception:
        pass
