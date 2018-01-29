#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters

from pdc.apps.module.models import Module
from pdc.apps.module.filters import ModuleFilterBase


class UnreleasedVariantFilter(ModuleFilterBase):
    variant_id      = django_filters.CharFilter(name='variant_id', lookup_type='iexact')
    variant_uid     = django_filters.CharFilter(name='uid', lookup_type='iexact')
    variant_name    = django_filters.CharFilter(name='name', lookup_type='iexact')
    variant_type    = django_filters.CharFilter(name='type', lookup_type='iexact')
    variant_version = django_filters.CharFilter(name='stream', lookup_type='iexact')
    variant_release = django_filters.CharFilter(name='version', lookup_type='iexact')
    variant_context = django_filters.CharFilter(name='context', lookup_type='iexact')

    class Meta:
        model = Module
        fields = ('koji_tag', 'modulemd', 'runtime_dep_name', 'runtime_dep_stream',
                  'build_dep_name', 'build_dep_stream', 'component_name', 'component_branch')
