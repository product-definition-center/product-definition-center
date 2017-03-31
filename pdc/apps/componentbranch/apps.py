#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from django.apps import AppConfig


class ComponentBranchConfig(AppConfig):
    name = 'pdc.apps.componentbranch'
    label = 'componentbranch'
    verbose_name = 'Component Branch'

    def ready(self):
        from pdc.apps.utils.utils import connect_app_models_pre_save_signal
        connect_app_models_pre_save_signal(self)
