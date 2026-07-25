from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_JSONL = tuple((ROOT / "evaluation").rglob("*.jsonl"))

EMAIL_RE = re.compile(r"(?i)\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
PHONE_CANDIDATE_RE = re.compile(r"(?<!\w)\+?\d[\d\s().-]{8,}\d(?!\w)")
WINDOWS_USER_PATH_RE = re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd)\s*[:=]\s*[\"']?"
        r"[A-Za-z0-9._~+/=-]{8,}"
    ),
)


class PublicDataPrivacyTests(unittest.TestCase):
    def test_public_jsonl_contains_no_direct_contact_data_or_local_paths(self) -> None:
        for path in PUBLIC_JSONL:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(EMAIL_RE.search(text), f"email-like value in {path}")
            self.assertIsNone(
                WINDOWS_USER_PATH_RE.search(text),
                f"local Windows user path in {path}",
            )

            for match in PHONE_CANDIDATE_RE.finditer(text):
                digits = re.sub(r"\D", "", match.group())
                looks_like_real_phone = 10 <= len(digits) <= 15 and len(set(digits)) >= 3
                self.assertFalse(
                    looks_like_real_phone,
                    f"phone-like value {match.group()!r} in {path}",
                )

    def test_public_jsonl_contains_no_common_secret_shapes(self) -> None:
        for path in PUBLIC_JSONL:
            text = path.read_text(encoding="utf-8")
            for pattern in SECRET_PATTERNS:
                self.assertIsNone(pattern.search(text), f"secret-like value in {path}")


if __name__ == "__main__":
    unittest.main()
