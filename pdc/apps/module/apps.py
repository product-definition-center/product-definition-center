#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig


class ModuleConfig(AppConfig):
    name = 'pdc.apps.module'

    def ready(self):
        from pdc.apps.utils.utils import connect_app_models_pre_save_signal
        connect_app_models_pre_save_signal(self)
