#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import re

from django.contrib.auth import models

import django_filters

from pdc.apps.common.filters import MultiValueFilter
from .models import GroupResourcePermission, ResourcePermission, ResourceApiUrl


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


class GroupResourcePermissionFilter(django_filters.FilterSet):
    group = MultiValueFilter(name='group__name')
    permission = MultiValueFilter(name='resource_permission__permission__name')
    resource = MultiValueFilter(name='resource_permission__resource__name')

    class Meta:
        model = GroupResourcePermission
        fields = ('group', 'resource', 'permission')


class ResourcePermissionFilter(django_filters.FilterSet):
    permission = MultiValueFilter(name='permission__name')
    resource = MultiValueFilter(name='resource__name')

    class Meta:
        model = ResourcePermission
        fields = ('resource', 'permission')


class ResourceFilter(MultiValueFilter):
    def filter(self, qs, value):
        for resource_name in value:
            regex = re.sub(r'{.*?}', r'(.*?)', resource_name)
            if regex != resource_name:
                qs = qs.filter(**{self.name + '__regex': regex})
            else:
                qs = super(ResourceFilter, self).filter(qs, value)
        return qs


class ResourceApiUrlFilter(django_filters.FilterSet):
    resource = ResourceFilter(name='resource__name')
    url = MultiValueFilter()

    class Meta:
        model = ResourceApiUrl
        fields = ('resource', 'url')
