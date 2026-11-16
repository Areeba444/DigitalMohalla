"""Upload checks (suite 27, unit part; ADR-0014; TC-59 EXIF stripped, TC-85 wrong type or size).

TC-260 to TC-264. Images are generated in memory; the GPS block is a made-up position.
"""

import io

import pytest
from PIL import Image

from app.domain.uploads.policy import InvalidUpload, check_and_strip, sniff

LIMIT = 5 * 1024 * 1024


def jpeg_with_gps() -> bytes:
    img = Image.new("RGB", (64, 48), (200, 120, 40))
    exif = Image.Exif()
    exif[0x010F] = "SyntheticCam"  # Make
    exif[0x8825] = {1: "N", 2: (31.0, 30.0, 0.0), 3: "E", 4: (74.0, 20.0, 0.0)}  # GPS IFD
    out = io.BytesIO()
    img.save(out, format="JPEG", exif=exif)
    return out.getvalue()


def test_tc260_gps_exif_is_removed() -> None:
    """Input: a JPEG whose EXIF has a camera make and a GPS position. Expected: the stored image
    has no EXIF at all and the same size (TC-59)."""
    raw = jpeg_with_gps()
    assert Image.open(io.BytesIO(raw)).getexif().get_ifd(0x8825)  # the input really has GPS
    clean = check_and_strip(raw, LIMIT)
    out = Image.open(io.BytesIO(clean.data))
    assert dict(out.getexif()) == {} and "exif" not in out.info
    assert (clean.mime, clean.width, clean.height) == ("image/jpeg", 64, 48)
    assert b"SyntheticCam" not in clean.data


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("WEBP", "image/webp")])
def test_tc261_png_and_webp_are_accepted(fmt: str, mime: str) -> None:
    img = Image.new("RGBA", (10, 10), (0, 0, 255, 128))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    assert check_and_strip(buf.getvalue(), LIMIT).mime == mime


@pytest.mark.parametrize(
    "data",
    [
        b"MZ\x90\x00 an executable renamed photo.jpg",
        b"%PDF-1.7 not accepted in iteration 2",
        b"GIF89a....",
        b"<svg xmlns='http://www.w3.org/2000/svg'/>",
    ],
)
def test_tc262_type_is_decided_by_content_not_by_name(data: bytes) -> None:
    """Expected: refused (TC-85) whatever the client calls it."""
    assert sniff(data) is None
    with pytest.raises(InvalidUpload, match="JPEG, PNG or WebP"):
        check_and_strip(data, LIMIT)


def test_tc263_size_and_empty_and_broken() -> None:
    with pytest.raises(InvalidUpload, match="larger"):
        check_and_strip(b"\xff\xd8\xff" + b"0" * 100, 50)
    with pytest.raises(InvalidUpload, match="empty"):
        check_and_strip(b"", LIMIT)
    with pytest.raises(InvalidUpload, match="could not be read"):
        check_and_strip(b"\xff\xd8\xff\xe0 truncated", LIMIT)


def test_tc264_decompression_bomb_is_refused() -> None:
    big = Image.new("L", (8000, 6000))  # 48 million pixels, small when compressed
    buf = io.BytesIO()
    big.save(buf, format="PNG")
    with pytest.raises(InvalidUpload, match="too many pixels"):
        check_and_strip(buf.getvalue(), LIMIT)
