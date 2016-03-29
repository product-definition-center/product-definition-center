#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import template
from datetime import datetime


def epochformat(value):
    if isinstance(value, (float, int)):
        dt = datetime.utcfromtimestamp(value)
    else:
        dt = value
    return dt.strftime("%Y-%m-%d %H:%M:%S")


register = template.Library()
register.filter('epochformat', epochformat)
