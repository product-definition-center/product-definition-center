#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import django_filters
from django.db.models import Q
from datetime import datetime

from pdc.apps.common.filters import CaseInsensitiveBooleanFilter
from pdc.apps.common import hacks
from pdc.apps.componentbranch.models import (
    ComponentBranch, SLA, SLAToComponentBranch)


def filter_active(queryset, name, value):
    if not value:
        return queryset
    try:
        processed_value = hacks.convert_str_to_bool(value)
    except ValueError:
        # If a ValueError is thrown, then the value was invalid
        return queryset

    today = datetime.utcnow().date()
    if processed_value is True:
        # Any branch that is active will have at least one SLA that has not
        # gone EOL
        return queryset.filter(slas__eol__gte=today).distinct()
    else:
        # This excludes the branches which contain at least one SLA that hasn't
        # gone EOL yet. This is used instead of the `exclude` Django method
        # for a huge performance increase
        where_extra_sql = (
            'NOT EXISTS (SELECT 1 FROM "{0}" WHERE "{1}"."id" = '
            '"{0}"."branch_id" AND "{0}"."eol" >= \'{2}\')'.format(
                SLAToComponentBranch._meta.db_table,
                ComponentBranch._meta.db_table, str(today)))
        # Any branch that is inactive will not have an SLA that has not gone
        # EOL yet. This checks for any branches which contain no SLAs or SLAs
        # that have gone EOL. It then excludes the branches which contain at
        # least one SLA that hasn't gone EOL yet.
        return queryset.filter(Q(slas__isnull=True) | Q(slas__eol__lte=today))\
            .extra(where=[where_extra_sql]).distinct()


def filter_active_sla_to_branch(queryset, name, value):
    if not value:
        return queryset
    try:
        processed_value = hacks.convert_str_to_bool(value)
    except ValueError:
        # If a ValueError is thrown, then the value was invalid
        return queryset

    today = datetime.utcnow().date()
    if processed_value is True:
        # Any branch that is active will have at least one SLA that has not
        # gone EOL
        return queryset.filter(branch__slas__eol__gte=today).distinct()
    else:
        # This excludes the branches which contain at least one SLA that hasn't
        # gone EOL yet. This is used instead of the `exclude` Django method
        # for a huge performance increase
        where_extra_sql = (
            'NOT EXISTS (SELECT 1 FROM "{0}" WHERE "{1}"."id" = '
            '"{0}"."branch_id" AND "{0}"."eol" >= \'{2}\')'.format(
                SLAToComponentBranch._meta.db_table,
                ComponentBranch._meta.db_table, str(today)))
        # Any branch that is inactive will not have an SLA that has not gone
        # EOL yet. This checks for any branches which contain no SLAs or SLAs
        # that have gone EOL. It then excludes the branches which contain at
        # least one SLA that hasn't gone EOL yet.
        return queryset.\
            filter(branch__slas__eol__lte=today).extra(where=[where_extra_sql]).distinct()


class ComponentBranchFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(name='name', lookup_expr='exact')
    global_component = django_filters.CharFilter(
        name='global_component__name', lookup_expr='exact')
    type = django_filters.CharFilter(
        name='type__name', lookup_expr='exact')
    active = CaseInsensitiveBooleanFilter(method=filter_active)
    critical_path = CaseInsensitiveBooleanFilter()

    class Meta:
        model = ComponentBranch
        exclude = ()


class SLAFilter(django_filters.FilterSet):

    class Meta:
        model = SLA
        # Specifies the exact lookups to allow
        fields = ('name', 'description')


class SLAToComponentBranchFilter(django_filters.FilterSet):
    sla = django_filters.CharFilter(name='sla__name', lookup_expr='exact')
    branch = django_filters.CharFilter(name='branch__name', lookup_expr='exact')
    global_component = django_filters.CharFilter(name='branch__global_component__name', lookup_expr='exact')
    branch_type = django_filters.CharFilter(name='branch__type__name', lookup_expr='exact')
    branch_active = CaseInsensitiveBooleanFilter(name='branch__active', method=filter_active_sla_to_branch)
    branch_critical_path = CaseInsensitiveBooleanFilter(name='branch__critical_path', lookup_expr='iexact')
    eol_after = django_filters.DateFilter(name="eol", lookup_expr='gte')
    eol_before = django_filters.DateFilter(name="eol", lookup_expr='lte')

    class Meta:
        model = SLAToComponentBranch
        # Specifies the exact lookups to allow
        fields = ('eol',)
