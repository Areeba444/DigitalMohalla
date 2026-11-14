"""StoragePort: where photo files live (ADR-0014; plan item M4).

Files never live in the database or on the API's own disk when deployed (Render's free disk does not
survive a redeploy). The port has three operations, `put`, `signed_url` and `get`, and two adapters
here:

- LocalDiskStorage for development and tests: files under a directory; a signed URL points back to
  the API (`GET /api/v1/files/{key}`) with an expiry time and an HMAC signature;
- UnavailableStorage when no storage is configured: every upload is refused with 503, and the
  handover or return goes on as checklist-only with a "reduced evidence" mark (FR-B-11).

An S3-compatible adapter for deployment follows the same port once the team has chosen a provider
by its free tier and terms, recorded on Form 13 with its secret in Render's settings (ADR-0014).
Keys are random; the original file name is never used. Files are never public.
"""

import hashlib
import hmac
import secrets
import time
from pathlib import Path
from typing import Protocol


class StorageUnavailable(Exception):
    """No photo storage is configured or it cannot be reached (503; checklist-only fallback)."""


class StoragePort(Protocol):
    def put(self, data: bytes, mime: str) -> str:
        """Store the bytes; returns a new random key."""
        ...

    def signed_url(self, key: str, ttl_seconds: int) -> tuple[str, int]:
        """A short-lived URL for one file and its expiry (epoch seconds)."""
        ...

    def get(self, key: str) -> bytes: ...


def new_key(mime: str) -> str:
    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(mime, "bin")
    return f"{secrets.token_hex(16)}.{ext}"


class LocalDiskStorage:
    def __init__(self, root: Path, secret: str) -> None:
        self.root = root
        self.secret = secret.encode()
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes, mime: str) -> str:
        key = new_key(mime)
        (self.root / key).write_bytes(data)
        return key

    def signed_url(self, key: str, ttl_seconds: int) -> tuple[str, int]:
        exp = int(time.time()) + ttl_seconds
        return f"/api/v1/files/{key}?exp={exp}&sig={self.signature(key, exp)}", exp

    def signature(self, key: str, exp: int) -> str:
        return hmac.new(self.secret, f"{key}:{exp}".encode(), hashlib.sha256).hexdigest()

    def verify(self, key: str, exp: int, sig: str) -> bool:
        return exp >= int(time.time()) and hmac.compare_digest(self.signature(key, exp), sig)

    def get(self, key: str) -> bytes:
        path = (self.root / key).resolve()
        if path.parent != self.root.resolve() or not path.is_file():  # no path tricks
            raise FileNotFoundError(key)
        return path.read_bytes()


class UnavailableStorage:
    def put(self, data: bytes, mime: str) -> str:
        raise StorageUnavailable("photo storage is not available; continue with the checklist")

    def signed_url(self, key: str, ttl_seconds: int) -> tuple[str, int]:
        raise StorageUnavailable("photo storage is not available")

    def get(self, key: str) -> bytes:
        raise StorageUnavailable("photo storage is not available")
