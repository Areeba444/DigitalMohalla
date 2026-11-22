"""Registration rules (UC-A1; FR-A-01; NFR-S-01; plan item F7). Pure, no I/O.

Plain-language rules:
- A guest gives a display name, an e-mail and a password, and must accept the terms and privacy notice.
- The password is 10 to 128 characters, is not only digits and does not contain the e-mail address
  or the part before the @ (so "name@example.test" cannot use "name2026name").
- The reply never says whether the e-mail was already registered (FR-A-01, UC-A1 ext 3a).
Passwords are hashed by `auth.hash_password`; the clear text is never stored or logged.
"""

import re
from dataclasses import dataclass

EMAIL_PATTERN = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
MIN_PASSWORD, MAX_PASSWORD = 10, 128
GENERIC_REPLY = "Check your e-mail to finish creating your account."


class InvalidRegistration(ValueError):
    """The form is incomplete or the password is too weak (nothing is created)."""


@dataclass(frozen=True)
class Registration:
    display_name: str
    email: str  # lower-cased, trimmed
    password: str


def validate(display_name: str, email: str, password: str, accepted_terms: bool) -> Registration:
    if not accepted_terms:  # UC-A1 ext 2a
        raise InvalidRegistration("accept the terms and the privacy notice to create an account")
    name = " ".join(display_name.split())
    if not 1 <= len(name) <= 80:
        raise InvalidRegistration("enter a display name of 1 to 80 characters")
    mail = email.strip().lower()
    if not EMAIL_PATTERN.match(mail) or len(mail) > 254:
        raise InvalidRegistration("enter a valid e-mail address")
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise InvalidRegistration(f"use a password of {MIN_PASSWORD} to {MAX_PASSWORD} characters")
    if password.isdigit():
        raise InvalidRegistration("a password cannot be only digits")
    local = mail.split("@", 1)[0]
    lowered = password.lower()
    if mail in lowered or (len(local) >= 4 and local in lowered):
        raise InvalidRegistration("a password cannot contain your e-mail address")
    return Registration(name, mail, password)
