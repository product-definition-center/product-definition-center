#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from functools import partial

from django.conf import settings
from django.forms import SelectMultiple
from django.core.exceptions import FieldError

import django_filters

from pdc.apps.common.filters import (MultiValueFilter, MultiIntFilter,
                                     NullableCharFilter, CaseInsensitiveBooleanFilter)
from . import models


def dependency_filter(type, queryset, value):
    m = models.Dependency.DEPENDENCY_PARSER.match(value)
    if not m:
        raise FieldError('Unrecognized value for filter for {}'.format(type))
    groups = m.groupdict()
    queryset = queryset.filter(dependency__name=groups['name'], dependency__type=type).distinct()
    for dep in models.Dependency.objects.filter(type=type, name=groups['name']):

        is_equal = dep.is_equal(groups['version']) if groups['version'] else False
        is_lower = dep.is_lower(groups['version']) if groups['version'] else False
        is_higher = dep.is_higher(groups['version']) if groups['version'] else False

        if groups['op'] == '=' and not dep.is_satisfied_by(groups['version']):
            queryset = queryset.exclude(pk=dep.rpm_id)

        # User requests everything depending on higher than X
        elif groups['op'] == '>' and dep.comparison in ('<', '<=', '=') and (is_lower or is_equal):
            queryset = queryset.exclude(pk=dep.rpm_id)

        # User requests everything depending on lesser than X
        elif groups['op'] == '<' and dep.comparison in ('>', '>=', '=') and (is_higher or is_equal):
            queryset = queryset.exclude(pk=dep.rpm_id)

        # User requests everything depending on at least X
        elif groups['op'] == '>=':
            if dep.comparison == '<' and (is_lower or is_equal):
                queryset = queryset.exclude(pk=dep.rpm_id)
            elif dep.comparison in ('<=', '=') and is_lower:
                queryset = queryset.exclude(pk=dep.rpm_id)

        # User requests everything depending on at most X
        elif groups['op'] == '<=':
            if dep.comparison == '>' and (is_higher or is_equal):
                queryset = queryset.exclude(pk=dep.rpm_id)
            elif dep.comparison in ('>=', '=') and is_higher:
                queryset = queryset.exclude(pk=dep.rpm_id)

    return queryset


class RPMFilter(django_filters.FilterSet):
    name        = MultiValueFilter()
    version     = MultiValueFilter()
    epoch       = MultiIntFilter()
    release     = MultiValueFilter()
    arch        = MultiValueFilter()
    srpm_name   = MultiValueFilter()
    srpm_nevra  = NullableCharFilter()
    filename    = MultiValueFilter()
    compose     = MultiValueFilter(name='composerpm__variant_arch__variant__compose__compose_id',
                                   distinct=True)
    linked_release = MultiValueFilter(name='linked_releases__release_id', distinct=True)
    provides = django_filters.MethodFilter(action=partial(dependency_filter,
                                                          models.Dependency.PROVIDES))
    requires = django_filters.MethodFilter(action=partial(dependency_filter,
                                                          models.Dependency.REQUIRES))
    obsoletes = django_filters.MethodFilter(action=partial(dependency_filter,
                                                           models.Dependency.OBSOLETES))
    conflicts = django_filters.MethodFilter(action=partial(dependency_filter,
                                                           models.Dependency.CONFLICTS))
    recommends = django_filters.MethodFilter(action=partial(dependency_filter,
                                                            models.Dependency.RECOMMENDS))
    suggests = django_filters.MethodFilter(action=partial(dependency_filter,
                                                          models.Dependency.SUGGESTS))
    has_no_deps = CaseInsensitiveBooleanFilter(name='dependency__isnull', distinct=True)

    class Meta:
        model = models.RPM
        fields = ('name', 'version', 'epoch', 'release', 'arch', 'srpm_name',
                  'srpm_nevra', 'compose', 'filename', 'linked_release',
                  'provides', 'requires', 'obsoletes', 'conflicts', 'recommends', 'suggests',
                  'has_no_deps')


class ImageFilter(django_filters.FilterSet):
    file_name           = MultiValueFilter()
    image_format        = MultiValueFilter(name='image_format__name')
    image_type          = MultiValueFilter(name='image_type__name')
    disc_number         = MultiIntFilter()
    disc_count          = MultiIntFilter()
    arch                = MultiValueFilter()
    mtime               = MultiIntFilter()
    size                = MultiIntFilter()
    implant_md5         = MultiValueFilter()
    volume_id           = MultiValueFilter()
    md5                 = MultiValueFilter()
    sha1                = MultiValueFilter()
    sha256              = MultiValueFilter()
    compose             = MultiValueFilter(name='composeimage__variant_arch__variant__compose__compose_id',
                                           distinct=True)
    bootable            = CaseInsensitiveBooleanFilter()

    class Meta:
        model = models.Image
        fields = ('file_name', 'image_format', 'image_type', 'disc_number',
                  'disc_count', 'arch', 'mtime', 'size', 'bootable',
                  'implant_md5', 'volume_id', 'md5', 'sha1', 'sha256')


class BuildImageFilter(django_filters.FilterSet):
    if settings.WITH_BINDINGS:
        component_name      = django_filters.MethodFilter(action='filter_by_component_name',
                                                          widget=SelectMultiple)
    else:
        component_name      = MultiValueFilter(name='rpms__srpm_name', distinct=True)
    rpm_version                 = MultiValueFilter(name='rpms__version', distinct=True)
    rpm_release                 = MultiValueFilter(name='rpms__release', distinct=True)

    image_id                = MultiValueFilter()
    image_format            = MultiValueFilter(name='image_format__name')
    md5                     = MultiValueFilter()

    archive_build_nvr       = MultiValueFilter(name='archives__build_nvr', distinct=True)
    archive_name            = MultiValueFilter(name='archives__name', distinct=True)
    archive_size            = MultiValueFilter(name='archives__size', distinct=True)
    archive_md5             = MultiValueFilter(name='archives__md5', distinct=True)
    release_id              = MultiValueFilter(name='releases__release_id', distinct=True)

    def filter_by_component_name(self, queryset, value):
        from pdc.apps.bindings import models as binding_models
        srpm_names = binding_models.ReleaseComponentSRPMNameMapping.objects.filter(
            release_component__name__in=value).distinct().values_list('srpm_name')
        if value:
            if srpm_names:
                return queryset.filter(rpms__srpm_name__in=srpm_names).distinct()
            else:
                return queryset.filter(rpms__srpm_name__in=value).distinct()
        else:
            return queryset

    class Meta:
        model = models.BuildImage
        fields = ('component_name', 'rpm_version', 'rpm_release', 'image_id', 'image_format', 'md5',
                  'archive_build_nvr', 'archive_name', 'archive_size', 'archive_md5', 'release_id')


class BuildImageRTTTestsFilter(django_filters.FilterSet):
    build_nvr = MultiValueFilter(name='image_id')
    test_result = MultiValueFilter(name='test_result__name')

    class Meta:
        model = models.BuildImage
        fields = ('build_nvr', 'test_result')
