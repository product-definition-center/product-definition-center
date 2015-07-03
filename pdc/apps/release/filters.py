#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters

from pdc.apps.common import filters
from .models import Release, ProductVersion, Product, ReleaseType, Variant


class ActiveReleasesFilter(django_filters.BooleanFilter):
    """
    Filter objects depending on whether their releases are active or not. If
    active=True, it will only keep objects with at least one active release.
    If active=False, it will keep only objects with no active releases.
    The `name` argument to __init__ should specify how to get to relases from
    the object.
    """
    def filter(self, qs, value):
        name = self.name + '__active'
        if value:
            return qs.filter(**{name: True}).distinct()
        else:
            return qs.exclude(**{name: True}).distinct()


class ReleaseFilter(django_filters.FilterSet):
    base_product = django_filters.CharFilter(name='base_product__base_product_id')
    has_base_product = django_filters.MethodFilter(action='find_has_base_product')
    release_type = django_filters.CharFilter(name='release_type__short')
    product_version = django_filters.CharFilter(name='product_version__product_version_id')
    integrated_with = filters.NullableCharFilter(name='integrated_with__release_id')

    class Meta:
        model = Release
        fields = ("release_id", "name", "short", "version", 'product_version',
                  "release_type", "base_product", 'active', 'integrated_with')

    def find_has_base_product(self, queryset, value, *args, **kwargs):
        """
        Make it possible to filter releases if base_product is null or not.
        """
        if value == 'True':
            return queryset.filter(base_product__isnull=False).distinct()
        elif value == 'False':
            return queryset.filter(base_product__isnull=True).distinct()
        return queryset


class ProductVersionFilter(django_filters.FilterSet):
    active = ActiveReleasesFilter(name='release')

    class Meta:
        model = ProductVersion
        fields = ('name', 'product_version_id', 'version', 'short', 'active')


class ProductFilter(django_filters.FilterSet):
    active = ActiveReleasesFilter(name='productversion__release')

    class Meta:
        model = Product
        fields = ('name', 'short', 'active')


class ReleaseTypeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_type="icontains")
    short = django_filters.CharFilter()

    class Meta:
        model = ReleaseType
        fields = ('name', 'short')


class ReleaseVariantFilter(django_filters.FilterSet):
    release = filters.MultiValueFilter(name='release__release_id')
    id      = filters.MultiValueFilter(name='variant_id')
    uid     = filters.MultiValueFilter(name='variant_uid')
    name    = filters.MultiValueFilter(name='variant_name')
    type    = filters.MultiValueFilter(name='variant_type__name')

    class Meta:
        model = Variant
        fields = ('release', 'id', 'uid', 'name', 'type')
