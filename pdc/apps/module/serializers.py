#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin
from .models import UnreleasedVariant, RuntimeDependency, BuildDependency

from pdc.apps.package.serializers import RPMRelatedField
from pdc.apps.package.models import RPM


class RuntimeDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuntimeDependency
        fields = ("dependency", "stream")


class BuildDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildDependency
        fields = ("dependency", "stream")


class UnreleasedVariantSerializer(StrictSerializerMixin,
                                  serializers.ModelSerializer):
    variant_id          = serializers.CharField(max_length=100)
    variant_uid         = serializers.CharField(max_length=200)
    variant_name        = serializers.CharField(max_length=300)
    variant_type        = serializers.CharField(max_length=100)
    variant_version     = serializers.CharField(max_length=100)
    variant_release     = serializers.CharField(max_length=100)
    # Default to '00000000' for now since this field will only be used once
    # other tooling is updated to supply this value. Eventually, this should
    # not have a default.
    variant_context     = serializers.CharField(max_length=100, default='00000000')
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
            'variant_version', 'variant_release', 'variant_context',
            'koji_tag', 'modulemd', 'runtime_deps', 'build_deps', 'active',
            'rpms',
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
