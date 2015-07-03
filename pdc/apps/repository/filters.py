#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters as filters

from pdc.apps.common.filters import MultiValueFilter
from . import models


class RepoFilter(filters.FilterSet):
    arch = filters.CharFilter(name='variant_arch__arch__name')
    content_category = filters.CharFilter(name='content_category__name')
    content_format = filters.CharFilter(name='content_format__name')
    release_id = filters.CharFilter(name='variant_arch__variant__release__release_id')
    variant_uid = filters.CharFilter(name='variant_arch__variant__variant_uid')
    repo_family = filters.CharFilter(name='repo_family__name')
    service = filters.CharFilter(name='service__name')
    shadow = filters.BooleanFilter()
    product_id = MultiValueFilter()

    class Meta:
        model = models.Repo
        fields = ('arch', 'content_category', 'content_format', 'name', 'release_id',
                  'repo_family', 'service', 'shadow', 'variant_uid', 'product_id')


class RepoFamilyFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_type="icontains")

    class Meta:
        model = models.RepoFamily
        fields = ('name',)
