# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import functools

from django import forms
from django.core.validators import EMPTY_VALUES
from django.db.models import Q
from django.utils import six
from django_filters.filterset import (BaseFilterSet,
                                      FilterSet,
                                      FilterSetMetaclass,
                                      FilterSetOptions)
import django_filters
import django.forms.widgets as widgets
import operator
from .models import Label, SigKey
from .hacks import convert_str_to_int

SelectMultiple = widgets.SelectMultiple


def value_is_not_empty(func):
    @functools.wraps(func)
    def _decorator(self, qs, value):
        if not value:
            return qs
        else:
            if value == ['']:
                value = []
            return func(self, qs, value)

    return _decorator


class MultiValueFilter(django_filters.MethodFilter):
    """
    Filter that allows multiple terms to be present and treats them as
    alternatives, i.e. it performs OR search.
    """
    def __init__(self, name=None, distinct=False):
        super(MultiValueFilter, self).__init__(action='filter', widget=SelectMultiple, name=name, distinct=distinct)

    @value_is_not_empty
    def filter(self, qs, value):
        qs = qs.filter(**{self.name + '__in': value})
        if self.distinct:
            qs = qs.distinct()
        return qs


class MultiValueRegexFilter(MultiValueFilter):
    """
    Filter that allows multiple terms to be present and treats them as
    alternatives with  regular expression match,
    i.e. it performs OR search.
    """
    @value_is_not_empty
    def filter(self, qs, value):
        condition_list = []
        for i in value:
            condition_list.append(Q(**{self.name + '__regex': i}))
        qs = qs.filter(reduce(operator.or_, condition_list))
        if self.distinct:
            qs = qs.distinct()
        return qs


class MultiIntFilter(MultiValueFilter):
    """
    MultiValueFilter that reports error when input is not a number.
    """
    @property
    def display_name(self):
        """
        Get name of the filter used by the user.
        """
        for name, filter in self.parent.filters.iteritems():
            if filter == self:
                return name
        # This should not happen, internal server error will be reported it if does.
        raise ValueError('Filter not defined in parent')

    @value_is_not_empty
    def filter(self, qs, value):
        # This can't actually call to parent method, as double invocation of
        # @value_is_not_empty would cause the filter with empty value to be
        # ignored.
        value = [convert_str_to_int(val, name=self.display_name) for val in value]
        qs = qs.filter(**{self.name + '__in': value})
        if self.distinct:
            qs = qs.distinct()
        return qs


class ComposeFilterSetOptions(FilterSetOptions):
    def __init__(self, options=None):
        # HACK NOTE:
        # class XXXFilterSet(FilterSet):
        # class Meta:
        # fields = ('A', 'B', 'C', 'D')
        # together = (('A', 'C'), ('B', 'D'))
        #
        # current can not support the crossing compose.
        self.together = getattr(options, 'together', None)
        super(ComposeFilterSetOptions, self).__init__(options)


class ComposeFilterSetMetaclass(FilterSetMetaclass):
    def __new__(cls, name, bases, attrs):
        super_class = super(ComposeFilterSetMetaclass, cls)
        new_class = super_class.__new__(cls, name, bases, attrs)
        new_class._meta = ComposeFilterSetOptions(
            getattr(new_class, 'Meta', None))
        return new_class


class PDCBaseFilterSet(six.with_metaclass(ComposeFilterSetMetaclass,
                                          FilterSet)):
    pass


class ComposeFilterSet(PDCBaseFilterSet):
    @BaseFilterSet.qs.getter
    def qs(self):
        """
        Copy from django-filter BaseFilterSet, we do a little hacking for
        supporting a compose fields query.
        """
        if not hasattr(self, '_qs'):
            together_cache = dict()
            valid = self.is_bound and self.form.is_valid()

            if self.strict and self.is_bound and not valid:
                self._qs = self.queryset.none()
                return self._qs

            # start with all the results and filter from there
            qs = self.queryset.all()
            for name, filter_ in six.iteritems(self.filters):
                value = None
                if valid:
                    value = self.form.cleaned_data[name]
                else:
                    raw_value = self.form[name].value()
                    try:
                        value = self.form.fields[name].clean(raw_value)
                    except forms.ValidationError:
                        # for invalid values either:
                        # strictly "apply" filter yielding no results and get outta here
                        if self.strict:
                            self._qs = self.queryset.none()
                            return self._qs
                        else:  # or ignore this filter altogether
                            pass

                if value is not None:  # valid & clean data
                    if self.is_together_field(name):
                        # HACK NOTE:
                        # together fields will be processed as one field, but the value would be a dict.
                        for together in self._meta.together:
                            if name in together:
                                if together in together_cache:
                                    data = together_cache[together]
                                    data['value'][name] = value
                                else:
                                    together_cache[together] = {
                                        'value': {
                                            name: value
                                        },
                                        'filter': filter_
                                    }
                    else:
                        qs = filter_.filter(qs, value)

            if self._meta.order_by:
                order_field = self.form.fields[self.order_by_field]
                data = self.form[self.order_by_field].data
                ordered_value = None
                try:
                    ordered_value = order_field.clean(data)
                except forms.ValidationError:
                    pass

                if ordered_value in EMPTY_VALUES and self.strict:
                    ordered_value = \
                        self.form.fields[self.order_by_field].choices[0][0]

                if ordered_value:
                    qs = qs.order_by(*self.get_order_by(ordered_value))

            if together_cache:
                for process_data in together_cache.itervalues():
                    filter = process_data['filter']
                    value = process_data['value']
                    qs = filter.filter(qs, value)

            self._qs = qs

        return self._qs

    def is_together_field(self, name):
        if not self._meta.together:
            return False

        for together in self._meta.together:
            if name in together:
                return True

        return False


class LabelFilter(FilterSet):
    name = MultiValueFilter()

    class Meta:
        model = Label
        fields = ('name',)


class SigKeyFilter(FilterSet):
    name = django_filters.CharFilter()
    key_id = django_filters.CharFilter()
    description = django_filters.CharFilter(lookup_type="icontains")

    class Meta:
        model = SigKey
        fields = ('name', 'key_id', 'description')


class NullableCharFilter(django_filters.CharFilter):
    NULL_STRINGS = ('Null', 'NULL', 'null', 'None')

    """
    Wrapper around CharFilter that allows filtering items with empty value.
    """
    def filter(self, qs, value):
        if value in self.NULL_STRINGS:
            args = {self.name + '__isnull': True}
            return qs.filter(**args)
        return super(NullableCharFilter, self).filter(qs, value)


class CaseInsensitiveBooleanFilter(django_filters.CharFilter):
    """
    Customize boolean filter that allows filtering items with below values:
    True: ('true', 't', '1'), regardless of letter case sensitive
    False: ('false', 'f', '0'), regardless of letter case sensitive
    for the other input, return empty queryset
    """
    TRUE_STRINGS = ('true', 't', '1')
    FALSE_STRINGS = ('false', 'f', '0')

    def filter(self, qs, value):
        if not value:
            return qs
        if value.lower() in self.TRUE_STRINGS:
            qs = qs.filter(**{self.name: True})
        elif value.lower() in self.FALSE_STRINGS:
            qs = qs.filter(**{self.name: False})
        else:
            qs = qs.none()
        if self.distinct:
            qs = qs.distinct()
        return qs
