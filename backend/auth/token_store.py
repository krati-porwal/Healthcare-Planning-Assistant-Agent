"""
TokenStore — In-Memory Access Token Registry
=============================================
Issues, validates, and revokes session-scoped access tokens.

Design decisions:
- UUID-based tokens (no JWT library dependency).
- Tokens expire after TOKEN_TTL_HOURS hours.
- Thread-safe via a module-level dict (single process; fine for academic use).
- A background cleanup is NOT needed — stale entries are pruned on access.
"""
import uuid
import datetime
from typing import Optional

TOKEN_TTL_HOURS: int = 8

# token_str -> {user_id, session_id, email, issued_at, expires_at}
_store: dict[str, dict] = {}


def issue_token(user_id: str, session_id: str, email: str) -> str:
    """
    Create and store a new access token for this user/session.

    Returns:
        The token string (format: hca-<uuid_hex>)
    """
    token = f"hca-{uuid.uuid4().hex}"
    now = datetime.datetime.utcnow()
    _store[token] = {
        "user_id":    user_id,
        "session_id": session_id,
        "email":      email,
        "issued_at":  now.isoformat() + "Z",
        "expires_at": (now + datetime.timedelta(hours=TOKEN_TTL_HOURS)).isoformat() + "Z",
    }
    print(f"[TokenStore] Token issued for user {user_id} (session {session_id}).")
    return token


def validate_token(token: Optional[str]) -> Optional[dict]:
    """
    Validate the token and return its payload if valid and not expired.

    Returns:
        Payload dict {user_id, session_id, email, issued_at, expires_at}
        or None if the token is missing, unknown, or expired.
    """
    if not token:
        return None

    payload = _store.get(token)
    if not payload:
        return None

    # Check expiry
    expires_at = datetime.datetime.fromisoformat(payload["expires_at"].rstrip("Z"))
    if datetime.datetime.utcnow() > expires_at:
        # Prune expired token
        _store.pop(token, None)
        print(f"[TokenStore] Token expired and removed.")
        return None

    return payload


def revoke_token(token: Optional[str]) -> bool:
    """
    Revoke (delete) the token from the store.

    Returns:
        True if the token existed and was removed, False otherwise.
    """
    if token and token in _store:
        user_id = _store[token].get("user_id", "?")
        _store.pop(token)
        print(f"[TokenStore] Token revoked for user {user_id}.")
        return True
    return False


def token_count() -> int:
    """Return the number of active tokens (useful for testing/debugging)."""
    return len(_store)
