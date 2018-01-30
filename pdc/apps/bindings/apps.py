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

        from pdc.apps.release.views import ReleaseViewSet
        filters.extend_release_filter(ReleaseViewSet)

        from pdc.apps.component.views import ReleaseComponentViewSet
        filters.extend_release_component_filter(ReleaseComponentViewSet)

    def _extend_serializers(self):
        from . import serializers

        from pdc.apps.release.views import ReleaseViewSet
        serializers.extend_release_serializer(ReleaseViewSet)

        from pdc.apps.component.views import ReleaseComponentViewSet
        serializers.extend_release_component_serializer(ReleaseComponentViewSet)
