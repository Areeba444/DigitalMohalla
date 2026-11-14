"""Upload checks and metadata stripping (ADR-0014; FR-B-11, NFR-S-06, NFR-PR-01; TC-59, TC-85; M4).

1. The type is decided by the file's first bytes, never by its name or the client's content type,
   so a renamed executable is refused (TC-85).
2. The size is checked against the configured limit before anything else is done (TC-85).
3. An image is decoded and re-encoded from its pixels alone, so no EXIF block, GPS position,
   camera serial, comment or embedded thumbnail can survive (TC-59). `metadata_stripped` is set only
   after this step.

Only JPEG, PNG and WebP photos are accepted in iteration 2. PDFs are allowed by the schema for
dispute statements, but their metadata cannot be stripped the same way, so they wait for iteration 3.
"""

import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
MAX_PIXELS = 40_000_000  # refuse decompression bombs before decoding (about 7000 x 5700)


class InvalidUpload(ValueError):
    """Wrong type, too large, empty or unreadable (422)."""


@dataclass(frozen=True)
class CleanImage:
    data: bytes
    mime: str
    width: int
    height: int


def sniff(data: bytes) -> str | None:
    """The MIME type from magic bytes, or None if it is not an accepted image."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def check_and_strip(data: bytes, max_bytes: int) -> CleanImage:
    if not data:
        raise InvalidUpload("the file is empty")
    if len(data) > max_bytes:
        raise InvalidUpload(f"the file is larger than {max_bytes // (1024 * 1024)} MB")
    mime = sniff(data)
    if mime is None:
        raise InvalidUpload("only JPEG, PNG or WebP photos are accepted")
    try:
        with Image.open(io.BytesIO(data)) as img:
            if img.width * img.height > MAX_PIXELS:
                raise InvalidUpload("the image has too many pixels")
            img.load()
            pixels = img.convert("RGBA" if img.mode in ("RGBA", "LA", "P") else "RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidUpload("the image could not be read") from exc
    fmt = FORMATS[mime]
    if fmt == "JPEG" and pixels.mode == "RGBA":
        pixels = pixels.convert("RGB")
    clean = Image.new(pixels.mode, pixels.size)  # a new image: pixels only, no info dictionary
    clean.paste(pixels)
    out = io.BytesIO()
    clean.save(out, format=fmt, **({"quality": 90} if fmt in ("JPEG", "WEBP") else {}))
    return CleanImage(out.getvalue(), mime, clean.width, clean.height)
