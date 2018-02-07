#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import django_filters

from pdc.apps.common.filters import CaseInsensitiveBooleanFilter, MultiValueFilter
from pdc.apps.module.models import Module


class ModuleFilterBase(django_filters.FilterSet):
    active              = CaseInsensitiveBooleanFilter()
    koji_tag            = django_filters.CharFilter(name='koji_tag', lookup_type='iexact')
    runtime_dep_name    = MultiValueFilter(name='runtime_deps__dependency', distinct=True)
    runtime_dep_stream  = MultiValueFilter(name='runtime_deps__stream', distinct=True)
    build_dep_name      = MultiValueFilter(name='build_deps__dependency', distinct=True)
    build_dep_stream    = MultiValueFilter(name='build_deps__stream', distinct=True)
    component_name      = MultiValueFilter(name='rpms__srpm_name', distinct=True)
    component_branch    = MultiValueFilter(name='rpms__srpm_commit_branch', distinct=True)
    rpm_filename        = MultiValueFilter(name='rpms__filename', distinct=True)


class ModuleFilter(ModuleFilterBase):
    uid                 = django_filters.CharFilter(name='uid', lookup_type='iexact')
    name                = django_filters.CharFilter(name='name', lookup_type='iexact')
    stream              = django_filters.CharFilter(name='stream', lookup_type='iexact')
    version             = django_filters.CharFilter(name='version', lookup_type='iexact')
    context             = django_filters.CharFilter(name='context', lookup_type='iexact')

    class Meta:
        model = Module
        fields = ('uid', 'name', 'stream', 'version', 'context', 'active', 'koji_tag',
                  'runtime_dep_name', 'runtime_dep_stream', 'build_dep_name', 'build_dep_stream',
                  'component_name', 'component_branch')
