#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = 'pdc.apps.auth'
    label = 'kerb_auth'
    verbose_name = 'Auth with Kerberos support'
