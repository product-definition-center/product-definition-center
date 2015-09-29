# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters

from pdc.apps.common.filters import (CaseInsensitiveBooleanFilter,
                                     MultiValueFilter)

from . import models


class OSBSFilter(django_filters.FilterSet):
    autorebuild = CaseInsensitiveBooleanFilter()
    release = MultiValueFilter(name='component__release__release_id')
    component_name = MultiValueFilter(name='component__name')

    class Meta:
        model = models.OSBSRecord
        fields = ('autorebuild', 'release', 'component_name')
