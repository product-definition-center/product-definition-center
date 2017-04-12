#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import django_filters

from pdc.apps.common.filters import CaseInsensitiveBooleanFilter, MultiValueFilter
from .models import (Tree, UnreleasedVariant)


class TreeFilter(django_filters.FilterSet):
    tree_id         = django_filters.CharFilter(name='tree_id', lookup_type='iexact')
    deleted         = CaseInsensitiveBooleanFilter()
    arch            = django_filters.CharFilter(name='arch__name', lookup_type='iexact')
    variant_uid     = django_filters.CharFilter(name='unreleasedvariant__variant_uid', lookup_type='iexact')
    content_format  = django_filters.CharFilter(name="content_format__name")

    class Meta:
        model = Tree
        fields = (
            'deleted',
            'tree_id',
            'tree_date',
            'variant',
            'arch',
            'content',
            'content_format',
            'url',
        )


class UnreleasedVariantFilter(django_filters.FilterSet):
    variant_id          = django_filters.CharFilter(name='variant_id', lookup_type='iexact')
    variant_uid         = django_filters.CharFilter(name='variant_uid', lookup_type='iexact')
    variant_name        = django_filters.CharFilter(name='variant_name', lookup_type='iexact')
    variant_type        = django_filters.CharFilter(name='variant_type', lookup_type='iexact')
    variant_version     = django_filters.CharFilter(name='variant_version', lookup_type='iexact')
    variant_release     = django_filters.CharFilter(name='variant_release', lookup_type='iexact')
    active              = CaseInsensitiveBooleanFilter()
    koji_tag            = django_filters.CharFilter(name='koji_tag', lookup_type='iexact')
    runtime_dep_name    = MultiValueFilter(name='runtime_deps__dependency', distinct=True)
    runtime_dep_stream  = MultiValueFilter(name='runtime_deps__stream', distinct=True)
    build_dep_name      = MultiValueFilter(name='build_deps__dependency', distinct=True)
    build_dep_stream    = MultiValueFilter(name='build_deps__stream', distinct=True)
    component_name      = MultiValueFilter(name='rpms__srpm_name', distinct=True)

    class Meta:
        model = UnreleasedVariant
        fields = ('variant_id', 'variant_uid', 'variant_name', 'variant_type',
                  'variant_version', 'variant_release', 'koji_tag',
                  'modulemd', 'runtime_dep_name', 'runtime_dep_stream',
                  'build_dep_name', 'build_dep_stream', 'component_name')
