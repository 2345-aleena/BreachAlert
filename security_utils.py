"""
security_utils.py
=================================================
The application's actual "brain" — pure logic, no HTTP concerns.
Kept separate from app.py so it can be unit-tested on its own and
swapped out easily (e.g. MOCK_BREACH_DB -> a real HaveIBeenPwned API
call in a later phase, without touching any route code).
"""

import math
import re

# ---------------------------------------------------------------
# Mock breach database.
#
# This simulates what a real breach-checking API (e.g. Have I Been
# Pwned) would return.
# ---------------------------------------------------------------
MOCK_BREACH_DB = {
    "demo@breachalert.app": [
        {"name": "SocialWeb 2019 Leak", "year": 2019, "records_exposed": "410M"},
        {"name": "ShopFast Data Incident", "year": 2022, "records_exposed": "2.1M"},
    ],
    "exposed@example.com": [
        {"name": "FitTrack Breach", "year": 2021, "records_exposed": "6.8M"},
    ],
}

COMMON_PASSWORDS = {
    "password", "123456", "123456789", "qwerty", "letmein",
    "111111", "12345678", "abc123", "password1", "admin",
}


def check_breach(email):
    """
    Looks up an email in the mock breach store.
    Returns a dict describing exposure.
    """
    normalized = email.strip().lower()
    breaches = MOCK_BREACH_DB.get(normalized, [])

    return {
        "email_checked": normalized,
        "breach_found": len(breaches) > 0,
        "breach_count": len(breaches),
        "breaches": breaches,
    }


def _shannon_entropy_bits(password):
    """Rough entropy estimate based on character-set size and length."""
    charset_size = 0
    if re.search(r"[a-z]", password):
        charset_size += 26
    if re.search(r"[A-Z]", password):
        charset_size += 26
    if re.search(r"[0-9]", password):
        charset_size += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        charset_size += 32

    if charset_size == 0:
        return 0.0

    return len(password) * math.log2(charset_size)


def analyze_password(password):
    """
    Scores a password's strength (0-100) and returns specific,
    actionable flags.
    """
    flags = []
    entropy = _shannon_entropy_bits(password)

    if len(password) < 8:
        flags.append("too_short")

    if password.lower() in COMMON_PASSWORDS:
        flags.append("common_password")

    if not re.search(r"[A-Z]", password):
        flags.append("no_uppercase")

    if not re.search(r"[0-9]", password):
        flags.append("no_number")

    if not re.search(r"[^a-zA-Z0-9]", password):
        flags.append("no_symbol")

    if re.search(r"(.)\1{2,}", password):
        flags.append("repeated_characters")

    score = min(100, round((entropy / 80) * 100))
    if "common_password" in flags:
        score = min(score, 10)
    if "too_short" in flags:
        score = min(score, 35)

    if score >= 80:
        strength_label = "strong"
    elif score >= 50:
        strength_label = "moderate"
    elif score >= 25:
        strength_label = "weak"
    else:
        strength_label = "very_weak"

    return {
        "score": score,
        "strength_label": strength_label,
        "entropy_bits": round(entropy, 1),
        "flags": flags,
    }


def calculate_security_score(breach_result, password_analysis):
    """
    Combines breach exposure and password strength into the single
    0-100 score shown on the frontend's scan card.
    """
    score = 100

    if breach_result["breach_found"]:
        penalty = min(50, 25 + (breach_result["breach_count"] - 1) * 10)
        score -= penalty

    if password_analysis is not None:
        score -= round((100 - password_analysis["score"]) * 0.4)

    return max(0, min(100, score))
