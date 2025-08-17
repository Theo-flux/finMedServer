from email.utils import parseaddr

from email_validator import EmailNotValidError, EmailSyntaxError
from pydantic import validate_email


def email_validator(value: str):
    try:
        validate_email(value)
        return value
    except EmailNotValidError:
        raise EmailSyntaxError("Invalid Email format")


def is_email(value):
    return "@" in parseaddr(value)[1]
