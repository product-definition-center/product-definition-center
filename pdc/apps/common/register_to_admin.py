#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
## admin.py ##

from pdc.apps.common.register_to_admin import register

# register models defined on each app
register('app1')

"""

from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered


def register(*app_list):
    for app_label in app_list:
        for model in apps.get_app_config(app_label).get_models():
            try:
                admin.site.register(model)
            except AlreadyRegistered:
                pass
