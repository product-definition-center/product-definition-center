#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import django_filters
from django.db.models import Q

from pdc.apps.common.filters import CaseInsensitiveBooleanFilter, MultiValueFilter, value_is_not_empty
from pdc.apps.module.models import Module
from pdc.apps.package.models import RPM


class ModuleComponentFilter(MultiValueFilter):
    """
    Multi-value filter for modules with an RPM with given name and branch.
    """
    @value_is_not_empty
    def _filter(self, qs, name, values):
        query = Q()

        for value in values:
            try:
                name, branch = value.split('/', 2)
                filters = {'name': name, 'srpm_commit_branch': branch}
            except ValueError:
                filters = {'name': value}

            rpms = RPM.objects.filter(**filters)
            query |= Q(rpms__in=rpms)

        qs = qs.filter(query)

        return qs


class ModuleFilterBase(django_filters.FilterSet):
    active              = CaseInsensitiveBooleanFilter()
    koji_tag            = django_filters.CharFilter(name='koji_tag', lookup_expr='iexact')
    runtime_dep_name    = MultiValueFilter(name='runtime_deps__dependency', distinct=True)
    runtime_dep_stream  = MultiValueFilter(name='runtime_deps__stream', distinct=True)
    build_dep_name      = MultiValueFilter(name='build_deps__dependency', distinct=True)
    build_dep_stream    = MultiValueFilter(name='build_deps__stream', distinct=True)
    component_name      = MultiValueFilter(name='rpms__srpm_name', distinct=True)
    component_branch    = MultiValueFilter(
        name='rpms__srpm_commit_branch', distinct=True,
        help_text="""
        Note that "component_name" filter can match different component than this filter.
        Use "component" filter instead to match both name and branch in a single component.
        """)
    component           = ModuleComponentFilter(
        help_text="""
        Match name and branch in a single component.
        Format is "<component_name>/<component_branch>" or just "<component_name>".
        """)
    rpm_filename        = MultiValueFilter(name='rpms__filename', distinct=True)


class ModuleFilter(ModuleFilterBase):
    uid                 = django_filters.CharFilter(name='uid', lookup_expr='iexact')
    name                = django_filters.CharFilter(name='name', lookup_expr='iexact')
    stream              = django_filters.CharFilter(name='stream', lookup_expr='iexact')
    version             = django_filters.CharFilter(name='version', lookup_expr='iexact')
    context             = django_filters.CharFilter(name='context', lookup_expr='iexact')

    class Meta:
        model = Module
        fields = ('uid', 'name', 'stream', 'version', 'context', 'active', 'koji_tag',
                  'runtime_dep_name', 'runtime_dep_stream', 'build_dep_name', 'build_dep_stream',
                  'component_name', 'component_branch', 'component')
