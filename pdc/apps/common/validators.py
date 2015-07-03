#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.core.exceptions import ValidationError
import string


def validate_md5(value):
    _validate_hex_string(value, 32)


def validate_sha1(value):
    _validate_hex_string(value, 40)


def validate_sha256(value):
    _validate_hex_string(value, 64)


def validate_sigkey(value):
    _validate_hex_string(value, 8)


def _validate_hex_string(value, requested_len):
    if any(c not in string.hexdigits for c in value):
        raise ValidationError('%s contains invalid characters' % value)
    if len(value) != requested_len:
        raise ValidationError('%s should be %d characters long' % (value, requested_len))
