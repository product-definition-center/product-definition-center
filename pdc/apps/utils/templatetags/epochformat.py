#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django import template
from datetime import datetime


def epochformat(value):
    dt = datetime.utcfromtimestamp(value)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


register = template.Library()
register.filter('epochformat', epochformat)
