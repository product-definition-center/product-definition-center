#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from functools import partial

from django.conf import settings
from django.core.exceptions import FieldError

import django_filters

from pdc.apps.common.filters import (MultiValueFilter, MultiIntFilter, MultiValueRegexFilter,
                                     NullableCharFilter, CaseInsensitiveBooleanFilter)
from pdc.apps.common.hacks import parse_epoch_version

from . import models


def dependency_predicate(op, version):
    """
    Returns function for comparing dependencies with given operator and
    version (e.g. ">=" "2.7" satisfies dependency "python<3.0").
    """
    if op == '=':
        def compare(dep_op, dep_version):
            if dep_op == '=':
                return version == dep_version
            if dep_op == '<':
                return version < dep_version
            if dep_op == '>':
                return version > dep_version
            if dep_op == '<=':
                return version <= dep_version
            if dep_op == '>=':
                return version >= dep_version
        return compare

    if op == '>':
        return lambda dep_op, dep_version: '>' in dep_op or dep_version > version

    if op == '<':
        return lambda dep_op, dep_version: '<' in dep_op or dep_version < version

    if op == '>=':
        return lambda dep_op, dep_version: \
            dependency_predicate('>', version)(dep_op, dep_version) or \
            dependency_predicate('=', version)(dep_op, dep_version)

    elif op == '<=':
        return lambda dep_op, dep_version: \
            dependency_predicate('<', version)(dep_op, dep_version) or \
            dependency_predicate('=', version)(dep_op, dep_version)

    raise FieldError('Unrecognized operator "{}" for {}'.format(op, type))


def dependency_filter(type, queryset, name, value):
    m = models.Dependency.DEPENDENCY_PARSER.match(value)
    if not m:
        raise FieldError('Unrecognized value for filter for {}'.format(type))

    groups = m.groupdict()
    name = groups['name']
    op = groups['op']
    version = groups['version']

    queryset = queryset.filter(dependency__name=name, dependency__type=type).distinct()

    if not version:
        return queryset

    version = parse_epoch_version(version)
    matches = dependency_predicate(op, version)
    deps = models.Dependency.objects.filter(type=type, name=name)

    for dep in deps:
        dep_version = dep.parsed_version
        if dep_version is not None and not matches(dep.comparison, dep_version):
            queryset = queryset.exclude(pk=dep.rpm_id)

    return queryset


class RPMFilter(django_filters.FilterSet):
    name        = MultiValueRegexFilter(
        help_text="""
            Multiple values will be OR-ed. Preferably use OR inside the regexp.
            """
    )
    version     = MultiValueFilter()
    epoch       = MultiIntFilter()
    release     = MultiValueFilter()
    arch        = MultiValueFilter()
    srpm_name   = MultiValueFilter()
    srpm_nevra  = NullableCharFilter()
    filename    = MultiValueFilter()
    compose     = MultiValueFilter(name='composerpm__variant_arch__variant__compose__compose_id',
                                   distinct=True)
    srpm_commit_hash = MultiValueFilter()
    srpm_commit_branch = MultiValueFilter()
    linked_release = MultiValueFilter(name='linked_releases__release_id', distinct=True)
    built_for_release = MultiValueFilter(name='built_for_release__release_id', distinct=True)
    provides = django_filters.CharFilter(method=partial(dependency_filter,
                                                        models.Dependency.PROVIDES))
    requires = django_filters.CharFilter(method=partial(dependency_filter,
                                                        models.Dependency.REQUIRES))
    obsoletes = django_filters.CharFilter(method=partial(dependency_filter,
                                                         models.Dependency.OBSOLETES))
    conflicts = django_filters.CharFilter(method=partial(dependency_filter,
                                                         models.Dependency.CONFLICTS))
    recommends = django_filters.CharFilter(method=partial(dependency_filter,
                                                          models.Dependency.RECOMMENDS))
    suggests = django_filters.CharFilter(method=partial(dependency_filter,
                                                        models.Dependency.SUGGESTS))
    has_no_deps = CaseInsensitiveBooleanFilter(
        name='dependency__isnull',
        distinct=True,
        help_text="""
    - If "true", lists only RPMs which do not have any dependencies.
    - If "false", lists only RPMs which have at least one dependency.
    """
    )

    class Meta:
        model = models.RPM
        fields = ('name', 'version', 'epoch', 'release', 'arch', 'srpm_name',
                  'srpm_nevra', 'compose', 'filename', 'linked_release', 'built_for_release',
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
    subvariant          = MultiValueFilter()
    compose             = MultiValueFilter(name='composeimage__variant_arch__variant__compose__compose_id',
                                           distinct=True)
    bootable            = CaseInsensitiveBooleanFilter()

    class Meta:
        model = models.Image
        fields = ('file_name', 'image_format', 'image_type', 'disc_number',
                  'disc_count', 'arch', 'mtime', 'size', 'bootable',
                  'implant_md5', 'volume_id', 'md5', 'sha1', 'sha256', 'subvariant')


class BuildImageFilter(django_filters.FilterSet):
    if settings.WITH_BINDINGS:
        component_name      = MultiValueFilter(method='filter_by_component_name')
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

    def filter_by_component_name(self, queryset, name, value):
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
    image_format = MultiValueFilter(name='image_format__name')

    class Meta:
        model = models.BuildImage
        fields = ('build_nvr', 'test_result', 'image_format')


class ReleasedFilesFilter(django_filters.FilterSet):
    released_date = MultiValueFilter()
    release_date = MultiValueFilter()
    zero_day_release = CaseInsensitiveBooleanFilter()
    obsolete = CaseInsensitiveBooleanFilter()
    file_primary_key = MultiIntFilter()
    repo = MultiValueFilter(name='repo__id')
    repo_name = MultiValueFilter(name='repo__name')
    release_id = MultiValueFilter(name='repo__variant_arch__variant__release__release_id')
    service = MultiValueFilter(name='repo__service__name')
    arch = MultiValueFilter(name='repo__variant_arch__arch__name')
    variant_uid = MultiValueFilter(name='repo__variant_arch__variant__variant_uid')
    release_date_after = django_filters.DateFilter(name="release_date", lookup_expr='gte')
    release_date_before = django_filters.DateFilter(name="release_date", lookup_expr='lte')
    released_date_after = django_filters.DateFilter(name="released_date", lookup_expr='gte')
    released_date_before = django_filters.DateFilter(name="released_date", lookup_expr='lte')

    class Meta:
        model = models.ReleasedFiles
        fields = ('released_date', 'release_date',
                  'file_primary_key', 'zero_day_release', 'obsolete', 'repo',
                  'repo_name', 'release_id', 'service', 'arch', 'variant_uid')
