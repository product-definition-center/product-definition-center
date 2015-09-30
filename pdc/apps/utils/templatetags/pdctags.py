#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import template
from django.conf import settings

from pdc import get_version


def pdc_version():
    return get_version()


def login_url(redirect=None):
    """Create login url based on settings.

    Optionally, append redirection URL.
    """
    url = settings.LOGIN_URL
    redirect = redirect or settings.LOGIN_REDIRECT_URL
    if redirect:
        url += '?next=' + redirect
    return url

register = template.Library()

register.simple_tag(pdc_version)
register.simple_tag(login_url)
