#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig


class OSBSConfig(AppConfig):
    name = 'pdc.apps.osbs'

    def ready(self):
        from . import signals   # noqa
