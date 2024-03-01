from django.core.exceptions import ValidationError

import re


def number_validator(password):
    regex = re.compile('[0-9]')
    if regex.search(password) is None:
        raise ValidationError("password must include number")


def letter_validator(password):
    lower_letter = re.compile('[a-z]')
    capital_letter = re.compile('[A-Z]')
    if lower_letter.search(password) is None or capital_letter.search(password) is None:
        raise ValidationError("password must include capital and lower letter")


def special_char_validator(password):
    regex = re.compile('[@_!#$%^&*()<>?/|}{~:]')
    if regex.search(password) is None:
        raise ValidationError("password must include special char")


def email_validator(email):
    if 'admin' in email:
        raise ValidationError("email can't be admin")


def username_validator(username):
    if username == 'admin':
        raise ValidationError("username can't be admin")
