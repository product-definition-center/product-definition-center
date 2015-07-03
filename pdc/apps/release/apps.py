#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig
from pdc.apps.utils.utils import connect_app_models_pre_save_signal


class ReleaseConfig(AppConfig):
    name = 'pdc.apps.release'

    def ready(self):
        models_name = ('ReleaseType', 'BaseProduct', 'Product', 'ProductVersion', 'Release', 'VariantType',
                       'Variant', 'VariantArch')
        connect_app_models_pre_save_signal(self, [self.get_model(model_name) for model_name in models_name])
