#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters as filters
from django.forms import SelectMultiple

from pdc.apps.common.filters import MultiValueFilter, MultiIntFilter, CaseInsensitiveBooleanFilter, value_is_not_empty
from pdc.apps.contact.models import Person
from . import models


class RepoFilter(filters.FilterSet):
    arch = MultiValueFilter(name='variant_arch__arch__name')
    content_category = MultiValueFilter(name='content_category__name')
    content_format = MultiValueFilter(name='content_format__name')
    release_id = MultiValueFilter(name='variant_arch__variant__release__release_id')
    variant_uid = MultiValueFilter(name='variant_arch__variant__variant_uid')
    repo_family = MultiValueFilter(name='repo_family__name')
    service = MultiValueFilter(name='service__name')
    shadow = CaseInsensitiveBooleanFilter()
    product_id = MultiIntFilter()
    name = MultiValueFilter(name='name')

    class Meta:
        model = models.Repo
        fields = ('arch', 'content_category', 'content_format', 'name', 'release_id',
                  'repo_family', 'service', 'shadow', 'variant_uid', 'product_id')


class RepoFamilyFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = models.RepoFamily
        fields = ('name',)


class PushTargetFilter(filters.FilterSet):
    name = MultiValueFilter()
    description = MultiValueFilter()
    host = MultiValueFilter()
    service = MultiValueFilter(name='service__name')

    class Meta:
        model = models.PushTarget
        fields = ('name', 'description', 'service', 'host')


class MultiDestinationFilter(filters.FilterSet):
    global_component = MultiValueFilter(name='global_component__name')
    origin_repo = MultiIntFilter()
    destination_repo = MultiIntFilter()
    origin_repo_name = MultiValueFilter(name='origin_repo__name')
    destination_repo_name = MultiValueFilter(name='destination_repo__name')
    origin_repo_release_id = MultiValueFilter(name='origin_repo__variant_arch__variant__release__release_id')
    destination_repo_release_id = MultiValueFilter(name='destination_repo__variant_arch__variant__release__release_id')
    subscribers = filters.MethodFilter(action='filter_by_subscribers', widget=SelectMultiple)
    active = CaseInsensitiveBooleanFilter()

    @value_is_not_empty
    def filter_by_subscribers(self, qs, value):
        people = Person.objects.filter(username__in=value)
        return qs.filter(subscribers__in=people)

    class Meta:
        model = models.MultiDestination
        fields = (
            'id',
            'global_component',
            'origin_repo',
            'destination_repo',
            'origin_repo_name',
            'destination_repo_name',
            'origin_repo_release_id',
            'destination_repo_release_id',
            'subscribers',
            'active',
        )
