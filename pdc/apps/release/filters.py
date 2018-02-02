#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import django_filters

from pdc.apps.common import filters
from .models import Release, ProductVersion, Product, ReleaseType, Variant, CPE, VariantCPE, BaseProduct, ReleaseGroup


class ActiveReleasesFilter(filters.CaseInsensitiveBooleanFilter):
    """
    Filter objects depending on whether their releases are active or not. If
    active=True, it will only keep objects with at least one active release.
    If active=False, it will keep only objects with no active releases.
    The `name` argument to __init__ should specify how to get to relases from
    the object.
    """

    help_text = """
    - If "true", show objects with at least one active release.
    - If "false", show objects with no active releases.
    """

    def _filter(self, qs, name, value):
        if not value:
            return qs
        self._validate_boolean(value)
        name = self.name + '__active'
        if value.lower() in self.TRUE_STRINGS:
            return qs.filter(**{name: True}).distinct()
        else:
            return qs.exclude(**{name: True}).distinct()


class AllowedPushTargetsFilter(filters.MultiValueFilter):
    def __init__(self, parent_names):
        super(AllowedPushTargetsFilter, self).__init__()
        self.parent_names = parent_names

    @filters.value_is_not_empty
    def _filter(self, qs, name, value):
        qs = qs.exclude(**{'masked_push_targets__name__in': value})
        prefix = ''
        for parent_name in self.parent_names:
            prefix += parent_name + '__'
            qs = qs.exclude(**{prefix + 'masked_push_targets__name__in': value})
        return qs.filter(**{prefix + 'product__allowed_push_targets__name__in': value})


class ReleaseFilter(django_filters.FilterSet):
    release_id = filters.MultiValueFilter(name='release_id')
    base_product = filters.MultiValueFilter(name='base_product__base_product_id')
    has_base_product = django_filters.CharFilter(method='find_has_base_product')
    release_type = filters.MultiValueFilter(name='release_type__short')
    product_version = filters.MultiValueFilter(name='product_version__product_version_id')
    integrated_with = filters.NullableCharFilter(name='integrated_with__release_id')
    active = filters.CaseInsensitiveBooleanFilter()
    name = filters.MultiValueFilter(name='name')
    short = filters.MultiValueFilter(name='short')
    version = filters.MultiValueFilter(name='version')
    sigkey = filters.MultiValueFilter(name='sigkey__key_id')
    allow_buildroot_push = filters.CaseInsensitiveBooleanFilter()
    allowed_debuginfo_services = filters.MultiValueFilter(name='allowed_debuginfo_services__name')
    allowed_push_targets = AllowedPushTargetsFilter(['product_version'])

    class Meta:
        model = Release
        fields = ("release_id", "name", "short", "version", 'product_version',
                  "release_type", "base_product", 'active', 'integrated_with',
                  'sigkey', 'allow_buildroot_push', 'allowed_debuginfo_services',
                  'allowed_push_targets')

    def find_has_base_product(self, queryset, name, value, *args, **kwargs):
        """
        Make it possible to filter releases if base_product is null or not.
        """
        if value == 'True':
            return queryset.filter(base_product__isnull=False).distinct()
        elif value == 'False':
            return queryset.filter(base_product__isnull=True).distinct()
        return queryset


class BaseProductFilter(django_filters.FilterSet):
    short               = filters.MultiValueFilter(name='short')
    version             = filters.MultiValueFilter(name='version')
    name                = filters.MultiValueFilter(name='name')
    base_product_id     = filters.MultiValueFilter(name='base_product_id')

    class Meta:
        model = BaseProduct
        fields = ("base_product_id", "short", "version", 'name')


class ProductVersionFilter(django_filters.FilterSet):
    active              = ActiveReleasesFilter(name='release')
    short               = filters.MultiValueFilter(name='short')
    version             = filters.MultiValueFilter(name='version')
    name                = filters.MultiValueFilter(name='name')
    product_version_id  = filters.MultiValueFilter(name='product_version_id')
    allowed_push_targets = AllowedPushTargetsFilter([])

    class Meta:
        model = ProductVersion
        fields = ('name', 'product_version_id', 'version', 'short', 'active', 'allowed_push_targets')


class ProductFilter(django_filters.FilterSet):
    active = ActiveReleasesFilter(name='productversion__release')
    name = filters.MultiValueFilter(name='name')
    short = filters.MultiValueFilter(name='short')
    allowed_push_targets = filters.MultiValueFilter(name='allowed_push_targets__name')

    class Meta:
        model = Product
        fields = ('name', 'short', 'active', 'allowed_push_targets')


class ReleaseTypeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    short = filters.MultiValueFilter(name='short')

    class Meta:
        model = ReleaseType
        fields = ('name', 'short')


class ReleaseVariantFilter(django_filters.FilterSet):
    release = filters.MultiValueFilter(name='release__release_id')
    id      = filters.MultiValueFilter(name='variant_id')
    uid     = filters.MultiValueFilter(name='variant_uid')
    name    = filters.MultiValueFilter(name='variant_name')
    type    = filters.MultiValueFilter(name='variant_type__name')
    variant_version = filters.MultiValueFilter(name='variant_version')
    variant_release = filters.MultiValueFilter(name='variant_release')
    allowed_push_targets = AllowedPushTargetsFilter(['release', 'product_version'])

    class Meta:
        model = Variant
        fields = ('release', 'id', 'uid', 'name', 'type', 'allowed_push_targets')


class CPEFilter(django_filters.FilterSet):
    cpe = filters.MultiValueFilter(name='cpe')
    description = filters.MultiValueFilter(name='description')

    class Meta:
        model = CPE
        fields = ('cpe', 'description')


class ReleaseVariantCPEFilter(django_filters.FilterSet):
    release = filters.MultiValueFilter(name='variant__release__release_id')
    variant_uid = filters.MultiValueFilter(name='variant__variant_uid')
    cpe = filters.MultiValueFilter(name='cpe__cpe')

    class Meta:
        model = VariantCPE
        fields = ('id', 'release', 'variant_uid', 'cpe')


class ReleaseGroupFilter(django_filters.FilterSet):
    name           = filters.MultiValueFilter(name='name')
    description    = filters.MultiValueFilter(name='description')
    type           = filters.MultiValueFilter(name='type__name')
    releases       = filters.MultiValueFilter(name='releases__release_id')
    active         = filters.CaseInsensitiveBooleanFilter()

    class Meta:
        model = ReleaseGroup
        fields = ('name', 'description', 'type', 'releases', 'active')
