#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters
from pdc.apps.common.filters import MultiValueFilter
from . import models


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
