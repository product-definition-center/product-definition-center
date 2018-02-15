#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AuthConfig(AppConfig):
    name = 'pdc.apps.auth'
    label = 'kerb_auth'
    verbose_name = 'Auth with Kerberos support'

    def ready(self, *args, **kwargs):
        from . import signals
        post_migrate.connect(signals.update_resources, sender=self)
