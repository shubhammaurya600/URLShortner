"""
shared/utils/base62.py

Stateless Base62 encoding/decoding and short code generation.

Design decisions:
  - Uses SHA-256 on (url + salt) so the same URL always gets the same code
    (deterministic), yet different salts generate different codes (collision retry).
  - Truncates to SHORT_CODE_LENGTH characters from the 7-char base.
  - Purely functional; no Django imports — safe to import anywhere.
"""
import hashlib
import string
from django.conf import settings

# ─────────────────────────────────────────────────
# Alphabet: 0-9, A-Z, a-z  → 62 characters
# ─────────────────────────────────────────────────
_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase
_BASE = len(_ALPHABET)  # 62


def encode(num: int) -> str:
    """
    Encode a non-negative integer into a Base62 string.

    Args:
        num: Non-negative integer to encode.

    Returns:
        Base62-encoded string (at least one character).
    """
    if num == 0:
        return _ALPHABET[0]
    digits: list[str] = []
    while num:
        num, remainder = divmod(num, _BASE)
        digits.append(_ALPHABET[remainder])
    return "".join(reversed(digits))


def decode(s: str) -> int:
    """
    Decode a Base62 string back to an integer.

    Args:
        s: Base62-encoded string.

    Returns:
        Decoded integer.

    Raises:
        ValueError: If the string contains characters outside the Base62 alphabet.
    """
    num = 0
    for char in s:
        idx = _ALPHABET.find(char)
        if idx == -1:
            raise ValueError(f"Invalid Base62 character: {char!r}")
        num = num * _BASE + idx
    return num


def generate_short_code(original_url: str, salt: str = "") -> str:
    """
    Generate a deterministic, Base62-encoded short code for a URL.

    Algorithm:
        1. Compute SHA-256 of (url + salt).
        2. Take the first 8 bytes of the digest → 64-bit integer.
        3. Base62-encode the integer.
        4. Return the first SHORT_CODE_LENGTH characters.

    Collision handling:
        The caller (UrlShortenerService) passes an incrementing salt so that
        each retry produces a different code for the same input URL.

    Args:
        original_url: The URL to shorten.
        salt: Optional salt string (e.g. "retry_1", "retry_2") for retry logic.

    Returns:
        A short code string of length SHORT_CODE_LENGTH (default 7).
    """
    length = getattr(settings, "SHORT_CODE_LENGTH", 7)
    digest = hashlib.sha256(f"{original_url}{salt}".encode()).hexdigest()
    # Take first 16 hex chars → 8 bytes → 64-bit integer → space of 62^7 ≈ 3.5T codes
    number = int(digest[:16], 16)
    code = encode(number)
    # Pad if somehow shorter than length (extremely rare edge case)
    code = code.zfill(length)
    return code[:length]
