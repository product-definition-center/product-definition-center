#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters

from django.db.models import Q
from django.forms import SelectMultiple
from django_filters import FilterSet, MethodFilter
from pdc.apps.common.filters import MultiValueFilter, MultiValueRegexFilter, value_is_not_empty

from . import models
from .models import (Person,
                     Maillist,
                     GlobalComponentContact,
                     ReleaseComponentContact)


class PersonFilterSet(django_filters.FilterSet):
    username = MultiValueFilter()
    email = MultiValueFilter()

    class Meta:
        model = models.Person
        fields = ('username', 'email')


class MaillistFilterSet(django_filters.FilterSet):
    mail_name = MultiValueFilter()
    email = MultiValueFilter()

    class Meta:
        model = models.Maillist
        fields = ('mail_name', 'email')


class ContactRoleFilterSet(django_filters.FilterSet):
    name = MultiValueFilter()

    class Meta:
        model = models.ContactRole
        fields = ('name',)


def _filter_contacts(people_filter, maillist_filter, qs, values):
    """Helper for filtering based on subclassed contacts.

    Runs the filter on separately on each subclass (field defined by argument,
    the same values are used), then filters the queryset to only keep items
    that have matching.
    """
    people = Person.objects.filter(**{people_filter + '__in': values})
    mailing_lists = Maillist.objects.filter(**{maillist_filter + '__in': values})
    return qs.filter(Q(contact__in=people) | Q(contact__in=mailing_lists))


class _BaseComponentContactFilter(FilterSet):
    contact = MethodFilter(action='filter_by_contact', widget=SelectMultiple)
    email = MethodFilter(action='filter_by_email', widget=SelectMultiple)
    role = MultiValueFilter(name='role__name')
    component = MultiValueRegexFilter(name='component__name')

    @value_is_not_empty
    def filter_by_contact(self, qs, value):
        return _filter_contacts('username', 'mail_name', qs, value)

    @value_is_not_empty
    def filter_by_email(self, qs, value):
        return _filter_contacts('email', 'email', qs, value)


class GlobalComponentContactFilter(_BaseComponentContactFilter):
    class Meta:
        model = GlobalComponentContact
        fields = ('role', 'email', 'contact', 'component')


class ReleaseComponentContactFilter(_BaseComponentContactFilter):
    dist_git_branch = MultiValueFilter(name='component__dist_git_branch')
    release = MultiValueFilter(name='component__release__release_id')
    global_component = MultiValueFilter(name='component__global_component__name')

    class Meta:
        model = ReleaseComponentContact
        fields = ('role', 'email', 'contact', 'component', 'dist_git_branch', 'release',
                  'global_component')
