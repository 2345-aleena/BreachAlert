"""
validators.py
=================================================
The Gatekeeper Layer.

"Never trust the client." Every value that enters the API through a
request body is checked here before any route handler is allowed to
use it. Nothing in app.py should trust request data that hasn't
passed through one of these functions first.

Each validator returns a tuple: (is_valid: bool, error_message: str | None)
"""

import re

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

MAX_EMAIL_LENGTH = 254
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 1


def validate_email(email):
    """Syntactic validation: is the shape of this string even an email?"""
    if email is None:
        return False, "Email is required."

    if not isinstance(email, str):
        return False, "Email must be a string."

    email = email.strip()

    if len(email) == 0:
        return False, "Email cannot be empty."

    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"Email must be {MAX_EMAIL_LENGTH} characters or fewer."

    if not EMAIL_PATTERN.match(email):
        return False, "Email format is invalid."

    return True, None


def validate_password_field(password):
    """
    Validates an OPTIONAL password field on the /scans endpoint.
    None is allowed (user chose not to test a password). If present,
    it must be a reasonably-sized string.
    """
    if password is None:
        return True, None

    if not isinstance(password, str):
        return False, "Password must be a string."

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be {MAX_PASSWORD_LENGTH} characters or fewer."

    return True, None


def validate_password_required(password):
    """
    Validates a REQUIRED password field on /passwords/analyze — this
    endpoint's entire purpose is analyzing a password, so it can't be
    optional here the way it is on /scans.
    """
    if password is None:
        return False, "Password is required."

    if not isinstance(password, str):
        return False, "Password must be a string."

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, "Password cannot be empty."

    if len(password) > MAX_PASSWORD_LENGTH:
        return False, f"Password must be {MAX_PASSWORD_LENGTH} characters or fewer."

    return True, None


def require_json_fields(payload, required_fields):
    """
    Generic guard used at the top of route handlers: confirms the
    request body is a JSON object and isn't missing required keys
    entirely (distinct from those keys having invalid values, which
    the specific validators above handle).
    """
    if not isinstance(payload, dict):
        return False, "Request body must be a JSON object."

    missing = [field for field in required_fields if field not in payload]
    if missing:
        return False, f"Missing required field(s): {', '.join(missing)}."

    return True, None
