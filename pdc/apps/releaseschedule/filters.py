#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters
from datetime import datetime

from pdc.apps.common.filters import CaseInsensitiveBooleanFilter
from pdc.apps.common import hacks
from pdc.apps.componentbranch.models import SLA
from .models import ReleaseSchedule


def filter_later_than_today(queryset, value):
    if not value:
        return queryset
    try:
        value = hacks.convert_str_to_bool(value)
    except ValueError:
        # If a ValueError is thrown, then the value was invalid
        return queryset
    today = datetime.utcnow().date()
    if value:
        op = "gte"
    else:
        op = "lt"
    lookup = "date__{}".format(op)
    return queryset.filter(**{lookup: today})


class ReleaseScheduleFilter(django_filters.FilterSet):
    release = django_filters.CharFilter(name='release__release_id', lookup_type='exact')
    product_version = django_filters.CharFilter(name='release__product_version__product_version_id', lookup_type='exact')
    sla = django_filters.ModelMultipleChoiceFilter(name="sla__name", queryset=SLA.objects.all(), to_field_name='name', lookup_type='exact')
    active = CaseInsensitiveBooleanFilter(name="date", action=filter_later_than_today)
    date_after = django_filters.DateFilter(name="date", lookup_type='gte')
    date_before = django_filters.DateFilter(name="date", lookup_type='lte')

    class Meta:
        model = ReleaseSchedule
        # Specifies additional exact lookups to allow
        fields = ["date"]
