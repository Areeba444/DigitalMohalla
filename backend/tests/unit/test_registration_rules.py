"""Registration rules (UC-A1; FR-A-01; plan item F7): pure, no database. All values are synthetic."""

import pytest

from app.domain.accounts.registration import InvalidRegistration, validate

GOOD = ("Sana Synthetic", "Sana@Example.Test", "a-long-synthetic-pass")


def test_a_good_form_is_normalised() -> None:
    form = validate("  Sana   Synthetic ", " Sana@Example.Test ", GOOD[2], True)
    assert (form.display_name, form.email) == ("Sana Synthetic", "sana@example.test")


def test_terms_must_be_accepted() -> None:  # UC-A1 ext 2a
    with pytest.raises(InvalidRegistration, match="terms"):
        validate(*GOOD, False)


@pytest.mark.parametrize("name", ["", "   ", "x" * 81])
def test_display_name_length(name: str) -> None:
    with pytest.raises(InvalidRegistration, match="display name"):
        validate(name, GOOD[1], GOOD[2], True)


@pytest.mark.parametrize(
    "mail", ["", "no-at-sign", "a@b", "two@@example.test", "spa ce@example.test"]
)
def test_email_must_look_like_an_email(mail: str) -> None:
    with pytest.raises(InvalidRegistration, match="e-mail"):
        validate(GOOD[0], mail, GOOD[2], True)


@pytest.mark.parametrize(
    "password",
    ["short", "123456789", "1234567890", "x" * 129, "my-sana@example.test-pass", "SANA-is-my-name"],
)
def test_weak_passwords_are_refused(password: str) -> None:
    with pytest.raises(InvalidRegistration):
        validate(GOOD[0], GOOD[1], password, True)


def test_a_short_local_part_does_not_block_ordinary_passwords() -> None:
    assert validate(GOOD[0], "ab@example.test", "unrelated-passphrase", True).email == (
        "ab@example.test"
    )
