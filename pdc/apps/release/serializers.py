#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers
from django.core.exceptions import FieldError

from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.common import models as common_models
from pdc.apps.common.serializers import StrictSerializerMixin
from .models import (Product, ProductVersion, Release,
                     BaseProduct, ReleaseType, Variant,
                     VariantArch, VariantType, ReleaseGroup, ReleaseGroupType)
from . import signals


class ProductSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    product_versions = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source='productversion_set',
        slug_field='product_version_id'
    )
    active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = ('name', 'short', 'active', 'product_versions')


class ProductVersionSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    product_version_id = serializers.CharField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    releases = serializers.SerializerMethodField()
    product = serializers.SlugRelatedField(slug_field='short',
                                           queryset=Product.objects.all())

    class Meta:
        model = ProductVersion
        fields = ('name', 'short', 'version', 'active', 'product_version_id', 'product', 'releases')

    def to_internal_value(self, data):
        if not self.partial and 'short' not in data:
            data['short'] = data.get('product')
        return super(ProductVersionSerializer, self).to_internal_value(data)

    def get_releases(self, obj):
        """[release_id]"""
        return [x.release_id for x in sorted(obj.release_set.all(), key=Release.version_sort_key)]


class ReleaseSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    release_type = ChoiceSlugField(slug_field='short',
                                   queryset=ReleaseType.objects.all())
    release_id = serializers.CharField(read_only=True)
    compose_set = serializers.SerializerMethodField()
    base_product = serializers.SlugRelatedField(slug_field='base_product_id',
                                                queryset=BaseProduct.objects.all(),
                                                required=False,
                                                default=None,
                                                allow_null=True)
    product_version = serializers.SlugRelatedField(slug_field='product_version_id',
                                                   queryset=ProductVersion.objects.all(),
                                                   required=False,
                                                   allow_null=True,
                                                   default=None)
    active = serializers.BooleanField(default=True)
    integrated_with = serializers.SlugRelatedField(slug_field='release_id',
                                                   queryset=Release.objects.all(),
                                                   required=False,
                                                   allow_null=True,
                                                   default=None)

    class Meta:
        model = Release
        fields = ('release_id', 'short', 'version', 'name', 'base_product',
                  'active', 'product_version', 'release_type',
                  'compose_set', 'integrated_with')

    def get_compose_set(self, obj):
        """[Compose.compose_id]"""
        return [compose.compose_id for compose in sorted(obj.get_all_composes())]

    def create(self, validated_data):
        signals.release_serializer_extract_data.send(sender=self, validated_data=validated_data)
        obj = super(ReleaseSerializer, self).create(validated_data)
        signals.release_serializer_post_create.send(sender=self, release=obj)
        return obj

    def update(self, instance, validated_data):
        signals.release_serializer_extract_data.send(sender=self, validated_data=validated_data)
        obj = super(ReleaseSerializer, self).update(instance, validated_data)
        signals.release_serializer_post_update.send(sender=self, release=obj)
        if hasattr(instance, 'pk'):
            # reload to make sure changes in mapping are reflected
            obj = Release.objects.get(pk=obj.pk)
        # By default, PUT does not erase optional field if not specified. This
        # loops over all optional fields and resets them manually.
        if not self.partial:
            for field_name, field in self.fields.iteritems():
                if not field.read_only and field_name not in validated_data:
                    attr = field.source or field_name
                    try:
                        if hasattr(obj, attr):
                            setattr(obj, attr, None)
                    except ValueError:
                        pass
        obj.save()
        return obj


class BaseProductSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    base_product_id = serializers.CharField(read_only=True)
    release_type = ChoiceSlugField(slug_field='short', queryset=ReleaseType.objects.all())

    class Meta:
        model = BaseProduct
        fields = ('base_product_id', 'short', 'version', 'name', 'release_type')


class ReleaseTypeSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    short = serializers.CharField()
    name = serializers.CharField()
    suffix = serializers.CharField()

    class Meta:
        model = ReleaseType
        fields = ("short", "name", "suffix",)


class VariantArchNestedSerializer(serializers.BaseSerializer):
    doc_format = "string"

    def to_representation(self, obj):
        return obj.arch.name

    def to_internal_value(self, data, files=None):
        try:
            arch = common_models.Arch.objects.get(name=data)
            return VariantArch(arch=arch)
        except common_models.Arch.DoesNotExist:
            raise FieldError('No such arch: "%s".' % data)


class ReleaseVariantSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    type    = ChoiceSlugField(source='variant_type', slug_field='name',
                              queryset=VariantType.objects.all())
    release = serializers.SlugRelatedField(slug_field='release_id',
                                           queryset=Release.objects.all())
    id      = serializers.CharField(source='variant_id')
    uid     = serializers.CharField(source='variant_uid')
    name    = serializers.CharField(source='variant_name')
    arches  = VariantArchNestedSerializer(source='variantarch_set',
                                          many=True)
    variant_version = serializers.CharField(allow_null=True, required=False)
    variant_release = serializers.CharField(allow_null=True, required=False)

    key_combination_error = 'add_arches/remove_arches can not be combined with arches.'

    extra_fields = ['add_arches', 'remove_arches']

    class Meta:
        model = Variant
        fields = ('release', 'id', 'uid', 'name', 'type', 'arches',
                  'variant_version', 'variant_release')

    def to_internal_value(self, data):
        # Save value of attributes not directly corresponding to serializer
        # fields. We can't rely on data dict to be mutable, so the values can
        # not be removed from it.
        self.add_arches = data.get('add_arches', None)
        self.remove_arches = data.get('remove_arches', None)
        return super(ReleaseVariantSerializer, self).to_internal_value(data)

    def update(self, instance, validated_data):
        arches = validated_data.pop('variantarch_set', [])
        instance = super(ReleaseVariantSerializer, self).update(instance, validated_data)
        if arches:
            if self.add_arches or self.remove_arches:
                raise FieldError(self.key_combination_error)
            # If arches were completely specified, try first to remove unwanted
            # arches, then create new ones.
            requested = dict([(x.arch.name, x) for x in arches])
            for variant in instance.variantarch_set.all():
                if variant.arch.name in requested:
                    del requested[variant.arch.name]
                else:
                    variant.delete()
            for arch in requested.values():
                arch.variant = instance
                arch.save()

        # These loops can only do something on partial update: when doing PUT,
        # "arches" is required and if any of the other arch modifications were
        # specified, an exception would be raised above.
        for arch_name in self.add_arches or []:
            arch = common_models.Arch.objects.get(name=arch_name)
            vararch = VariantArch(arch=arch, variant=instance)
            vararch.save()

        for arch_name in self.remove_arches or []:
            instance.variantarch_set.filter(arch__name=arch_name).delete()

        return instance


class VariantTypeSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = VariantType
        fields = ('name',)


class ReleaseGroupSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    description         = serializers.CharField(required=True)
    type                = ChoiceSlugField(slug_field='name',
                                          queryset=ReleaseGroupType.objects.all())
    releases            = ChoiceSlugField(slug_field='release_id',
                                          many=True, queryset=Release.objects.all(),
                                          allow_null=True, required=False, default=[])
    active              = serializers.BooleanField(default=True)

    class Meta:
        model = ReleaseGroup
        fields = ('name', 'description', 'type', 'releases', 'active')

    def to_internal_value(self, data):
        releases = data.get('releases', [])
        for release in releases:
            try:
                Release.objects.get(release_id=release)
            except Release.DoesNotExist:
                raise serializers.ValidationError({'detail': 'release %s does not exist' % release})

        return super(ReleaseGroupSerializer, self).to_internal_value(data)
