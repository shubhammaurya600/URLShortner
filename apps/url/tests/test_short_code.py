"""
apps/url/tests/test_short_code.py

Unit tests for the Base62 short code generator.
No database, no external services needed.
"""
import string
from django.test import SimpleTestCase

from shared.utils.base62 import decode, encode, generate_short_code


class TestBase62Encoder(SimpleTestCase):
    """Tests for encode() / decode() round-trip."""

    def test_encode_zero(self):
        self.assertEqual(encode(0), "0")

    def test_encode_positive_integer(self):
        result = encode(12345)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_encode_large_integer(self):
        big = 2**32
        encoded = encode(big)
        self.assertIsInstance(encoded, str)
        self.assertEqual(decode(encoded), big)

    def test_decode_roundtrip(self):
        for n in [0, 1, 61, 62, 63, 1000, 3_521_614_606_207]:
            self.assertEqual(decode(encode(n)), n)

    def test_decode_invalid_char_raises(self):
        with self.assertRaises(ValueError):
            decode("!invalid!")

    def test_alphabet_boundary(self):
        """62 encodes to '10' in base62."""
        self.assertEqual(encode(62), "10")
        self.assertEqual(decode("10"), 62)


class TestGenerateShortCode(SimpleTestCase):
    """Tests for generate_short_code()."""

    def test_returns_correct_length(self):
        code = generate_short_code("https://example.com")
        self.assertEqual(len(code), 7)  # default SHORT_CODE_LENGTH

    def test_deterministic_without_salt(self):
        """Same URL + no salt should always produce the same code."""
        url = "https://deterministic.example.com/path"
        self.assertEqual(generate_short_code(url), generate_short_code(url))

    def test_different_urls_different_codes(self):
        self.assertNotEqual(
            generate_short_code("https://a.com"),
            generate_short_code("https://b.com"),
        )

    def test_salt_changes_code(self):
        url = "https://example.com/collision"
        code_no_salt = generate_short_code(url, salt="")
        code_with_salt = generate_short_code(url, salt="retry_1")
        self.assertNotEqual(code_no_salt, code_with_salt)

    def test_different_salts_different_codes(self):
        url = "https://example.com"
        codes = {generate_short_code(url, salt=f"retry_{i}") for i in range(10)}
        self.assertEqual(len(codes), 10)

    def test_only_base62_chars(self):
        base62 = string.digits + string.ascii_uppercase + string.ascii_lowercase
        code = generate_short_code("https://example.com/test")
        for ch in code:
            self.assertIn(ch, base62, f"Non-base62 character found: {ch!r}")
