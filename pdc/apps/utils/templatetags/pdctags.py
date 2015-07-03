#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import template

from pdc import get_version


def pdc_version():
    return get_version()

register = template.Library()

register.simple_tag(pdc_version)
