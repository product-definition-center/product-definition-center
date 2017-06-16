#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.common.models import Arch
from pdc.apps.common.serializers import StrictSerializerMixin, DynamicFieldsSerializerMixin
from pdc.apps.common.fields import ChoiceSlugField
from .models import (UnreleasedVariant, RuntimeDependency, BuildDependency)

from pdc.apps.repository.models import ContentFormat
from pdc.apps.package.serializers import RPMRelatedField, RPMSerializer
from pdc.apps.package.models import RPM


class UnreleasedVariantField(serializers.Field):

    def to_internal_value(self, data):
        try:
            variant = UnreleasedVariant.objects.get(variant_uid=data['variant_uid'], variant_version=data['variant_version'], variant_release=data['variant_release'])
        except UnreleasedVariant.DoesNotExist:
            raise serializers.ValidationError("UnreleasedVariant %s does not exist.")
        return variant

    def to_representation(self, value):
        return {'variant_uid': value.variant_uid, 'variant_name': value.variant_name}


class JSONSerializerField(serializers.Field):
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class RuntimeDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuntimeDependency
        fields = ("dependency", "stream")


class BuildDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildDependency
        fields = ("dependency", "stream")


class UnreleasedVariantSerializer(StrictSerializerMixin,
                                  DynamicFieldsSerializerMixin,
                                  serializers.ModelSerializer):
    variant_id          = serializers.CharField(max_length=100)
    variant_uid         = serializers.CharField(max_length=200)
    variant_name        = serializers.CharField(max_length=300)
    variant_type        = serializers.CharField(max_length=100)
    variant_version     = serializers.CharField(max_length=100)
    variant_release     = serializers.CharField(max_length=100)
    active              = serializers.BooleanField(default=False)
    koji_tag            = serializers.CharField(max_length=300)
    modulemd            = serializers.CharField()
    runtime_deps        = RuntimeDepSerializer(many=True, required=False)
    build_deps          = BuildDepSerializer(many=True, required=False)
    rpms                = RPMRelatedField(many=True, read_only=False,
                                          queryset=RPM.objects.all(),
                                          required=False)

    class Meta:
        model = UnreleasedVariant
        fields = (
            'variant_id', 'variant_uid', 'variant_name', 'variant_type',
            'variant_version', 'variant_release', 'koji_tag', 'modulemd',
            'runtime_deps', 'build_deps', 'active', 'rpms',
        )

    def validate(self, attrs):
        # TODO: validate
        return attrs

    def create(self, validated_data):
        runtime_deps_data = validated_data.pop('runtime_deps', [])
        build_deps_data = validated_data.pop('build_deps', [])
        rpm_data = validated_data.pop('rpms', [])

        variant = UnreleasedVariant.objects.create(**validated_data)

        for dep_data in runtime_deps_data:
            RuntimeDependency.objects.create(variant=variant, **dep_data)

        for dep_data in build_deps_data:
            BuildDependency.objects.create(variant=variant, **dep_data)

        for rpm in rpm_data:
            variant.rpms.add(rpm)

        return variant
