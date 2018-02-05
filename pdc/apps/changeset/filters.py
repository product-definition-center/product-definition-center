#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django.forms.widgets as widgets

from django.utils import timezone
from django.utils.dateparse import parse_datetime

import django_filters

from pdc.apps.common.filters import MultiValueFilter, value_is_not_empty
from . import models


def _date_time_with_timezone(value):
    date_time = parse_datetime(value)
    if date_time is None:
        return value
    return timezone.make_aware(date_time)


def _filter_committed(qs, lookup_expr, value):
    date_time = _date_time_with_timezone(value)
    filter_args = {'committed_on__' + lookup_expr: date_time}
    return qs.filter(**filter_args).distinct()


class ChangesetFilterSet(django_filters.FilterSet):
    author = MultiValueFilter(name='author__username', distinct=True)
    resource = MultiValueFilter(name='change__target_class', distinct=True)
    changed_since = django_filters.CharFilter(method='filter_committed_since',
                                              widget=widgets.DateTimeInput)
    changed_until = django_filters.CharFilter(method='filter_committed_until',
                                              widget=widgets.DateTimeInput)
    comment = django_filters.CharFilter(name="comment", lookup_expr="contains")

    @value_is_not_empty
    def filter_committed_since(self, qs, name, value):
        return _filter_committed(qs, 'gte', value)

    @value_is_not_empty
    def filter_committed_until(self, qs, name, value):
        return _filter_committed(qs, 'lte', value)

    class Meta:
        model = models.Changeset
        fields = ('author', 'resource', 'changed_since', 'changed_until', 'comment')
