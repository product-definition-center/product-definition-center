#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.common.models import Arch
from pdc.apps.common.serializers import StrictSerializerMixin, DynamicFieldsSerializerMixin
from pdc.apps.common.fields import ChoiceSlugField
from .models import (Tree, UnreleasedVariant, RuntimeDependency,
                     BuildDependency)

#from pdc.apps.release.models import Release
from pdc.apps.repository.models import ContentFormat

class UnreleasedVariantField(serializers.Field):
    #doc_format = "UnreleasedVariant.variant_uid"

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

class TreeSerializer(StrictSerializerMixin,
                        serializers.ModelSerializer):

    tree_id             = serializers.CharField()
    tree_date           = serializers.DateField()
    variant             = UnreleasedVariantField()
    arch                = serializers.SlugRelatedField(slug_field='name', queryset=Arch.objects.all())
    deleted             = serializers.BooleanField(default=False)
    content             = JSONSerializerField()
    content_format      = ChoiceSlugField(slug_field='name', many=True, queryset=ContentFormat.objects.all())
    url                 = serializers.CharField()

    class Meta:
        model = Tree
        fields = (
            'tree_id', 'tree_date', 'variant', 'arch',  'deleted', 'content', 'content_format', 'url',
        )

    def validate(self, attrs):
        # TODO: validate
        return attrs


class RuntimeDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuntimeDependency
        fields = ("dependency",)


class BuildDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildDependency
        fields = ("dependency",)


class UnreleasedVariantSerializer(StrictSerializerMixin,
                        DynamicFieldsSerializerMixin,
                        serializers.ModelSerializer):
    variant_id          = serializers.CharField(max_length=100)
    variant_uid         = serializers.CharField(max_length=200)
    variant_name        = serializers.CharField(max_length=300)
    variant_type        = serializers.CharField(max_length=100)
    variant_version     = serializers.CharField(max_length=100)
    variant_release     = serializers.CharField(max_length=100)
    koji_tag            = serializers.CharField(max_length=300)
    runtime_deps        = RuntimeDepSerializer(many=True)
    build_deps          = BuildDepSerializer(many=True)

    class Meta:
        model = UnreleasedVariant
        fields = (
            'variant_id', 'variant_uid', 'variant_name', 'variant_type',
            'variant_version', 'variant_release', 'koji_tag',
            'runtime_deps', 'build_deps',
        )


    def validate(self, attrs):
        # TODO: validate
        return attrs

    def create(self, validated_data):
        runtime_deps_data = validated_data.pop('runtime_deps', [])
        build_deps_data = validated_data.pop('build_deps', [])

        variant = UnreleasedVariant.objects.create(**validated_data)

        for dep_data in runtime_deps_data:
            RuntimeDependency.objects.create(variant=variant, **dep_data)

        for dep_data in build_deps_data:
            BuildDependency.objects.create(variant=variant, **dep_data)

        return variant
