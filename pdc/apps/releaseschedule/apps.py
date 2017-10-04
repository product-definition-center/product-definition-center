#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig


class ReleaseScheduleConfig(AppConfig):
    name = 'pdc.apps.releaseschedule'
    verbose_name = 'Release Schedule App'

    def ready(self):
        from pdc.apps.utils.utils import connect_app_models_pre_save_signal
        connect_app_models_pre_save_signal(self)
