#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc.apps.utils.rpm import parse_nvr, parse_nvra

import django_filters
from django.db.models import Q
from django.core.exceptions import ValidationError

from pdc.apps.common.filters import value_is_not_empty, MultiValueFilter, CaseInsensitiveBooleanFilter, \
    MultiValueCaseInsensitiveFilter
from .models import Compose, OverrideRPM, ComposeTree, ComposeImage, VariantArch


class ComposeFilter(django_filters.FilterSet):
    release             = MultiValueCaseInsensitiveFilter(name='release__release_id')
    compose_id          = MultiValueCaseInsensitiveFilter(name='compose_id')
    compose_type        = MultiValueCaseInsensitiveFilter(name='compose_type__name')
    acceptance_testing  = MultiValueFilter(name='acceptance_testing__name')
    rpm_nvr             = django_filters.MethodFilter(action="filter_nvr")
    rpm_nvra            = django_filters.MethodFilter(action="filter_nvra")
    deleted             = CaseInsensitiveBooleanFilter()
    compose_date        = MultiValueFilter(name='compose_date')
    compose_respin      = MultiValueFilter(name='compose_respin')
    compose_label       = MultiValueFilter(name='compose_label')
    # TODO: return only latest compose

    @value_is_not_empty
    def filter_nvr(self, qs, value):
        try:
            nvr = parse_nvr(value)
        except ValueError:
            raise ValidationError("Invalid NVR: %s" % value)

        q = Q()
        q &= Q(variant__variantarch__composerpm__rpm__name=nvr["name"])
        q &= Q(variant__variantarch__composerpm__rpm__version=nvr["version"])
        q &= Q(variant__variantarch__composerpm__rpm__release=nvr["release"])
        return qs.filter(q).distinct()

    @value_is_not_empty
    def filter_nvra(self, qs, value):
        try:
            nvra = parse_nvra(value)
        except ValueError:
            raise ValidationError("Invalid NVRA: %s" % value)

        q = Q()
        q &= Q(variant__variantarch__composerpm__rpm__name=nvra["name"])
        q &= Q(variant__variantarch__composerpm__rpm__version=nvra["version"])
        q &= Q(variant__variantarch__composerpm__rpm__release=nvra["release"])
        q &= Q(variant__variantarch__composerpm__rpm__arch=nvra["arch"])
        return qs.filter(q).distinct()

    class Meta:
        model = Compose
        fields = ('deleted', 'compose_id', 'compose_date', 'compose_respin',
                  'compose_label', 'release', 'compose_type', 'acceptance_testing')


class OverrideRPMFilter(django_filters.FilterSet):
    release     = MultiValueCaseInsensitiveFilter(name='release__release_id')
    comment     = django_filters.CharFilter(lookup_expr='icontains')
    arch        = MultiValueFilter(name='arch')
    variant     = MultiValueFilter(name='variant')
    srpm_name   = MultiValueFilter(name='srpm_name')
    rpm_name    = MultiValueFilter(name='rpm_name')
    rpm_arch    = MultiValueFilter(name='rpm_arch')

    class Meta:
        model = OverrideRPM
        fields = ('release', 'variant', 'arch', 'srpm_name', 'rpm_name', 'rpm_arch', 'comment')


class ComposeTreeFilter(django_filters.FilterSet):
    compose         = MultiValueCaseInsensitiveFilter(name='compose__compose_id')
    variant         = MultiValueCaseInsensitiveFilter(name='variant__variant_uid')
    arch            = MultiValueCaseInsensitiveFilter(name='arch__name')
    location        = MultiValueCaseInsensitiveFilter(name='location__short')
    scheme          = MultiValueCaseInsensitiveFilter(name='scheme__name')

    class Meta:
        model = ComposeTree
        fields = ('compose', 'variant', 'arch', 'location', 'scheme')


class ComposeTreeRTTTestFilter(django_filters.FilterSet):
    compose         = MultiValueFilter(name='variant__compose__compose_id')
    variant         = MultiValueFilter(name='variant__variant_uid')
    arch            = MultiValueFilter(name='arch__name')
    test_result     = MultiValueFilter(name='rtt_testing_status__name')

    class Meta:
        model = VariantArch
        fields = ('compose', 'variant', 'arch', 'test_result')


class ComposeImageRTTTestFilter(django_filters.FilterSet):
    compose         = MultiValueFilter(name='variant_arch__variant__compose__compose_id')
    variant         = MultiValueFilter(name='variant_arch__variant__variant_uid')
    arch            = MultiValueFilter(name='variant_arch__arch__name')
    file_name       = MultiValueFilter(name='image__file_name')
    test_result     = MultiValueFilter(name='rtt_test_result__name')

    class Meta:
        model = ComposeImage
        fields = ('compose', 'variant', 'arch', 'file_name', 'test_result')
