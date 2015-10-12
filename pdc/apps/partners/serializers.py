# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.release import models as release_models
from . import models


class PartnerTypeSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.PartnerType
        fields = ('name', )


class PartnerSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    type = ChoiceSlugField(slug_field='name',
                           queryset=models.PartnerType.objects.all())

    class Meta:
        model = models.Partner
        fields = ('short', 'name', 'binary', 'source', 'type', 'enabled',
                  'ftp_dir', 'rsync_dir')


class VariantArchField(StrictSerializerMixin, serializers.ModelSerializer):
    release = serializers.CharField(source='variant.release.release_id')
    variant = serializers.CharField(source='variant.variant_uid')
    arch = serializers.CharField(source='arch.name')

    class Meta:
        model = release_models.VariantArch
        fields = ('release', 'variant', 'arch')

    def to_internal_value(self, data):
        try:
            return release_models.VariantArch.objects.get(
                variant__release__release_id=data['release'],
                variant__variant_uid=data['variant'],
                arch__name=data['arch']
            )
        except release_models.VariantArch.DoesNotExist:
            raise serializers.ValidationError(
                'No VariantArch for release_id={release}, variant_uid={variant}, arch={arch}'.format(**data)
            )


class PartnerMappingSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    partner = serializers.SlugRelatedField(slug_field='short',
                                           queryset=models.Partner.objects.all())
    variant_arch = VariantArchField()

    class Meta:
        model = models.PartnerMapping
        fields = ('partner', 'variant_arch')
