#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig


class BindingsConfig(AppConfig):
    name = 'pdc.apps.bindings'
    label = 'bindings'
    verbose_name = 'Bindings for various models'

    def ready(self):
        self._extend_filters()
        self._extend_serializers()

        self._connect_signals()

    def _connect_signals(self):
        from pdc.apps.utils.utils import connect_app_models_pre_save_signal
        models_name = ('ReleaseBugzillaMapping', 'ReleaseDistGitMapping', 'ReleaseComponentSRPMNameMapping')
        connect_app_models_pre_save_signal(self, [self.get_model(model_name) for model_name in models_name])

    def _extend_filters(self):
        from . import filters
        from pdc.apps.release import filters as release_filters
        filters.extend_release_filter(release_filters.ReleaseFilter)
        from pdc.apps.component import filters as component_filters
        filters.extend_release_component_filter(component_filters.ReleaseComponentFilter)

    def _extend_serializers(self):
        from . import serializers
        from pdc.apps.release import serializers as release_serializers
        serializers.extend_release_serializer(release_serializers.ReleaseSerializer)
        from pdc.apps.component import serializers as component_serializers
        serializers.extend_release_component_serializer(component_serializers.ReleaseComponentSerializer)
