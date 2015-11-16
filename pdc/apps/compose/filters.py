#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import kobo.rpmlib

import django_filters
from django.db.models import Q
from django.core.exceptions import ValidationError

from pdc.apps.common.filters import value_is_not_empty
from .models import Compose, OverrideRPM, ComposeTree


class ComposeFilter(django_filters.FilterSet):
    release             = django_filters.CharFilter(name='release__release_id', lookup_type='iexact')
    compose_id          = django_filters.CharFilter(name='compose_id', lookup_type='iexact')
    compose_type        = django_filters.CharFilter(name='compose_type__name', lookup_type='iexact')
    acceptance_testing  = django_filters.CharFilter(name='acceptance_testing__name')
    srpm_name           = django_filters.CharFilter(name='variant__variantarch__composerpm__rpm__srpm_name',
                                                    lookup_type='iexact',
                                                    distinct=True)
    rpm_name            = django_filters.CharFilter(name='variant__variantarch__composerpm__rpm__name',
                                                    lookup_type='iexact',
                                                    distinct=True)
    rpm_version         = django_filters.CharFilter(name='variant__variantarch__composerpm__rpm__version',
                                                    lookup_type='iexact',
                                                    distinct=True)
    rpm_release         = django_filters.CharFilter(name='variant__variantarch__composerpm__rpm__release',
                                                    lookup_type='iexact',
                                                    distinct=True)
    rpm_arch            = django_filters.CharFilter(name='variant__variantarch__composerpm__rpm__arch',
                                                    lookup_type='iexact',
                                                    distinct=True)
    rpm_nvr             = django_filters.MethodFilter(action="filter_nvr")
    rpm_nvra            = django_filters.MethodFilter(action="filter_nvra")
    # TODO: return only latest compose

    @value_is_not_empty
    def filter_nvr(self, qs, value):
        try:
            nvr = kobo.rpmlib.parse_nvr(value)
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
            nvra = kobo.rpmlib.parse_nvra(value)
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
    release = django_filters.CharFilter(name='release__release_id', lookup_type='iexact')
    comment = django_filters.CharFilter(lookup_type='icontains')

    class Meta:
        model = OverrideRPM
        fields = ('release', 'variant', 'arch', 'srpm_name', 'rpm_name', 'rpm_arch', 'comment')


class ComposeTreeFilter(django_filters.FilterSet):
    compose         = django_filters.CharFilter(name='compose__compose_id', lookup_type='iexact')
    variant         = django_filters.CharFilter(name='variant__variant_uid', lookup_type='iexact')
    arch            = django_filters.CharFilter(lookup_type='iexact')
    location        = django_filters.CharFilter(name='location__short', lookup_type='iexact')
    scheme          = django_filters.CharFilter(name='scheme__name', lookup_type='iexact')

    class Meta:
        model = ComposeTree
        fields = ('compose', 'variant', 'arch', 'location', 'scheme')
