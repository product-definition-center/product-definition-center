#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib.auth import models

import django_filters

from pdc.apps.common.filters import MultiValueFilter


class PermissionFilter(django_filters.FilterSet):
    codename        = MultiValueFilter()
    app_label       = MultiValueFilter(name='content_type__app_label',
                                       distinct=True)
    model           = MultiValueFilter(name='content_type__model',
                                       distinct=True)

    class Meta:
        model = models.Permission
        fields = ('codename', 'app_label', 'model')


class GroupFilter(django_filters.FilterSet):
    name                  = MultiValueFilter()
    permission_codename   = MultiValueFilter(name='permissions__codename',
                                             distinct=True)
    permission_app_label  = MultiValueFilter(name='permissions__content_type__app_label',
                                             distinct=True)
    permission_model      = MultiValueFilter(name='permissions__content_type__model',
                                             distinct=True)

    class Meta:
        model = models.Group
        fields = ('name', 'permission_codename',
                  'permission_app_label', 'permission_model')
