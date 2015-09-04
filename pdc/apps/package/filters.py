#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings
from django.forms import SelectMultiple

import django_filters

from pdc.apps.common.filters import MultiValueFilter, MultiIntFilter, NullableCharFilter
from . import models


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

    class Meta:
        model = models.RPM
        fields = ('name', 'version', 'epoch', 'release', 'arch', 'srpm_name',
                  'srpm_nevra', 'compose', 'filename', 'linked_release')


class ImageFilter(django_filters.FilterSet):
    file_name           = MultiValueFilter()
    image_format        = MultiValueFilter(name='image_format__name')
    image_type          = MultiValueFilter(name='image_type__name')
    disc_number         = MultiValueFilter()
    disc_count          = MultiValueFilter()
    arch                = MultiValueFilter()
    mtime               = MultiValueFilter()
    size                = MultiValueFilter()
    implant_md5         = MultiValueFilter()
    volume_id           = MultiValueFilter()
    md5                 = MultiValueFilter()
    sha1                = MultiValueFilter()
    sha256              = MultiValueFilter()
    compose             = MultiValueFilter(name='composeimage__variant_arch__variant__compose__compose_id',
                                           distinct=True)

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
