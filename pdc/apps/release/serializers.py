#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers
from django.core.exceptions import FieldError
from django.conf import settings

from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.common import models as common_models
from pdc.apps.common.serializers import StrictSerializerMixin
from .models import (Product, ProductVersion, Release,
                     BaseProduct, ReleaseType, Variant, CPE, VariantCPE,
                     VariantArch, VariantType, ReleaseGroup, ReleaseGroupType,
                     validateCPE)
from . import signals
from pdc.apps.common.models import SigKey
from pdc.apps.repository.models import PushTarget, Service


def convert_push_targets_to_mask(data, instance, parent_key):
    """
    Converts "allowed_push_targets" in data to "masked_push_targets" (depending on data in parent).
    """
    if 'allowed_push_targets' in data:
        parent = data.get(parent_key)
        if parent is None and instance is not None:
            parent = getattr(instance, parent_key)

        allowed_push_targets = set(data.pop('allowed_push_targets'))
        available_push_targets = set(parent.allowed_push_targets.all()) if parent else set()
        invalid_push_targets = [
            push_target.name for push_target in allowed_push_targets - available_push_targets]
        if invalid_push_targets:
            raise serializers.ValidationError(
                {'detail': 'Push targets must be allowed in parent %s: %s' % (parent_key, invalid_push_targets)})

        data['masked_push_targets'] = list(available_push_targets - allowed_push_targets)


class CPEField(serializers.CharField):
    """ Serializer for CPE strings (starts with "cpe:") """
    doc_format = "string"

    def to_internal_value(self, data):
        verified_data = super(CPEField, self).to_internal_value(data)
        error = validateCPE(verified_data)
        if error:
            raise serializers.ValidationError({'detail': error})
        return verified_data


def allowed_push_targets_field(parent_key):
    if parent_key:
        help_text = 'Allowed push targets (subset from parent %s)' % parent_key
    else:
        help_text = 'Allowed push targets'

    return serializers.SlugRelatedField(
        many=True,
        slug_field='name',
        queryset=PushTarget.objects.all(),
        default=[],
        help_text=help_text)


class ProductSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    product_versions = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        source='productversion_set',
        slug_field='product_version_id'
    )
    active = serializers.BooleanField(read_only=True)
    allowed_push_targets = allowed_push_targets_field(parent_key=None)

    class Meta:
        model = Product
        fields = ('name', 'short', 'active', 'product_versions', 'allowed_push_targets')


class ProductVersionSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    product_version_id = serializers.CharField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    releases = serializers.SerializerMethodField()
    product = serializers.SlugRelatedField(slug_field='short',
                                           queryset=Product.objects.all())
    allowed_push_targets = allowed_push_targets_field(parent_key='product')

    class Meta:
        model = ProductVersion
        fields = ('name', 'short', 'version', 'active', 'product_version_id', 'product', 'releases', 'allowed_push_targets')

    def to_internal_value(self, data):
        data = data.copy()
        if not self.partial and 'short' not in data:
            data['short'] = data.get('product')
        return super(ProductVersionSerializer, self).to_internal_value(data)

    def get_releases(self, obj):
        """["Release.release_id"]"""
        return [x.release_id for x in sorted(obj.release_set.all(), key=Release.version_sort_key)]

    def validate(self, data):
        convert_push_targets_to_mask(data, self.instance, 'product')
        return data


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
    sigkey = serializers.SlugRelatedField(slug_field='key_id',
                                          queryset=SigKey.objects.all(),
                                          required=False,
                                          allow_null=True,
                                          default=None)
    allow_buildroot_push = serializers.BooleanField(default=False)
    allowed_debuginfo_services = ChoiceSlugField(slug_field='name',
                                                 many=True, queryset=Service.objects.all(),
                                                 required=False, default=[])
    allowed_push_targets = allowed_push_targets_field(parent_key='product version')

    class Meta:
        model = Release
        fields = ('release_id', 'short', 'version', 'name', 'base_product',
                  'active', 'product_version', 'release_type',
                  'compose_set', 'integrated_with', 'sigkey', 'allow_buildroot_push',
                  'allowed_debuginfo_services', 'allowed_push_targets')

    def set_default_sigkey(self, validated_data):
        if hasattr(settings, 'RELEASE_DEFAULT_SIGKEY'):
            if "sigkey" in validated_data and not validated_data["sigkey"]:
                validated_data["sigkey"], _ = SigKey.objects.get_or_create(key_id=settings.RELEASE_DEFAULT_SIGKEY)
        return validated_data

    def get_compose_set(self, obj):
        """["Compose.compose_id"]"""
        return [compose.compose_id for compose in sorted(obj.get_all_composes())]

    def create(self, validated_data):
        signals.release_serializer_extract_data.send(sender=self, validated_data=validated_data)
        validated_data = self.set_default_sigkey(validated_data)
        obj = super(ReleaseSerializer, self).create(validated_data)
        signals.release_serializer_post_create.send(sender=self, release=obj)
        return obj

    def update(self, instance, validated_data):
        signals.release_serializer_extract_data.send(sender=self, validated_data=validated_data)
        validated_data = self.set_default_sigkey(validated_data)
        obj = super(ReleaseSerializer, self).update(instance, validated_data)
        signals.release_serializer_post_update.send(sender=self, release=obj)
        if hasattr(instance, 'pk'):
            # reload to make sure changes in mapping are reflected
            obj = Release.objects.get(pk=obj.pk)
        obj.save()
        return obj

    def validate(self, data):
        convert_push_targets_to_mask(data, self.instance, 'product_version')
        return data


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
    doc_format = "Arch.name"

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
    allowed_push_targets = allowed_push_targets_field(parent_key='release')

    key_combination_error = 'add_arches/remove_arches can not be combined with arches.'

    extra_fields = ['add_arches', 'remove_arches']

    class Meta:
        model = Variant
        fields = ('release', 'id', 'uid', 'name', 'type', 'arches',
                  'variant_version', 'variant_release', 'allowed_push_targets')

    def to_internal_value(self, data):
        # Save value of attributes not directly corresponding to serializer
        # fields. We can't rely on data dict to be mutable, so the values can
        # not be removed from it.
        self.add_arches = data.get('add_arches', None)
        self.remove_arches = data.get('remove_arches', None)
        return super(ReleaseVariantSerializer, self).to_internal_value(data)

    def create(self, validated_data):
        arches = validated_data.pop('variantarch_set', [])
        instance = super(ReleaseVariantSerializer, self).create(validated_data)
        self._add_arches(instance, arches)
        return instance

    def update(self, instance, validated_data):
        arches = validated_data.pop('variantarch_set', [])
        instance = super(ReleaseVariantSerializer, self).update(instance, validated_data)
        self._add_arches(instance, arches)

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

    def validate(self, data):
        convert_push_targets_to_mask(data, self.instance, 'release')
        return data

    def _add_arches(self, instance, arches):
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


class CPESerializer(StrictSerializerMixin, serializers.ModelSerializer):
    cpe = CPEField(allow_blank=False, allow_null=False, required=True)
    description = serializers.CharField(allow_blank=True, allow_null=False, required=False)

    class Meta:
        model = CPE
        fields = ('id', 'cpe', 'description')

    def create(self, validated_data):
        cpe = validated_data['cpe']
        if CPE.objects.filter(cpe=cpe).exists():
            raise serializers.ValidationError({'detail': ['CPE "%s" already exists.' % cpe]})
        return super(CPESerializer, self).create(validated_data)


class ReleaseVariantCPESerializer(StrictSerializerMixin, serializers.ModelSerializer):
    release = serializers.CharField(source='variant.release.release_id')
    variant_uid = serializers.CharField(source='variant.variant_uid')
    cpe = CPEField(allow_blank=False, allow_null=False, required=True)

    class Meta:
        model = VariantCPE
        fields = ('id', 'release', 'variant_uid', 'cpe')

    def create(self, validated_data):
        variant = validated_data['variant']
        cpe = validated_data['cpe']
        if VariantCPE.objects.filter(variant=variant, cpe=cpe).exists():
            raise serializers.ValidationError(
                {'detail': ['CPE(%s) binding for variant "%s" already exists.' % (cpe, variant)]})
        return super(ReleaseVariantCPESerializer, self).create(validated_data)

    def to_internal_value(self, data):
        verified_data = super(ReleaseVariantCPESerializer, self).to_internal_value(data)

        variant = verified_data.get('variant')
        if variant is not None:
            if 'release' in variant:
                release_id = variant['release']['release_id']
            else:
                release_id = self.instance.variant.release.release_id

            if 'variant_uid' in variant:
                variant_uid = variant['variant_uid']
            else:
                variant_uid = self.instance.variant.variant_uid

            try:
                verified_data['variant'] = Variant.objects.get(release__release_id=release_id, variant_uid=variant_uid)
            except Variant.DoesNotExist:
                raise serializers.ValidationError(
                    {'detail': 'variant (release=%s, uid=%s) does not exist' % (release_id, variant_uid)})

        cpe = verified_data.get('cpe')
        if cpe is not None:
            try:
                verified_data['cpe'] = CPE.objects.get(cpe=cpe)
            except CPE.DoesNotExist:
                raise serializers.ValidationError({'detail': 'cpe "%s" does not exist' % cpe})

        return verified_data


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
