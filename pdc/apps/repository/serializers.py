#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from . import models
from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.common.hacks import convert_str_to_int
from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.component.models import GlobalComponent
from pdc.apps.contact.models import Person
from pdc.apps.release import models as release_models


class RepoSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    release_id       = serializers.CharField(source='variant_arch.variant.release.release_id')
    variant_uid      = serializers.CharField(source='variant_arch.variant.variant_uid')
    arch             = serializers.CharField(source='variant_arch.arch.name')
    service          = ChoiceSlugField(slug_field='name',
                                       queryset=models.Service.objects.all())
    repo_family      = ChoiceSlugField(slug_field='name',
                                       queryset=models.RepoFamily.objects.all())
    content_format   = ChoiceSlugField(slug_field='name',
                                       queryset=models.ContentFormat.objects.all())
    content_category = ChoiceSlugField(slug_field='name',
                                       queryset=models.ContentCategory.objects.all())
    name             = serializers.CharField()
    shadow           = serializers.BooleanField(required=False, default=False)
    product_id       = serializers.IntegerField(required=False, default=None, allow_null=True)

    class Meta:
        model = models.Repo
        fields = ('id', 'release_id', 'variant_uid', 'arch', 'service', 'repo_family',
                  'content_format', 'content_category', 'name', 'shadow', 'product_id')

    def validate(self, attrs):
        try:
            variant_arch = attrs.get('variant_arch', {})
            release_id  = variant_arch.get('variant', {}).get('release', {}).get('release_id', '')
            variant_uid = variant_arch.get('variant', {}).get('variant_uid', '')
            arch        = variant_arch.get('arch', {}).get('name', '')
            if self.instance and self.partial:
                variantarch = self.instance.variant_arch
                release_id = release_id or variantarch.variant.release.release_id
                variant_uid = variant_uid or variantarch.variant.variant_uid
                arch = arch or variantarch.arch.name
            attrs['variant_arch'] = release_models.VariantArch.objects.get(
                variant__release__release_id=release_id,
                variant__variant_uid=variant_uid,
                arch__name=arch
            )
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                'No VariantArch for release_id=%s, variant_uid=%s, arch=%s'
                % (release_id, variant_uid, arch)
            )
        if not self.instance:
            # Validate repo name.
            instance = models.Repo(**attrs)
            instance.clean()
            # Validate repo is unique.
            try:
                models.Repo.objects.get(**attrs)
                raise serializers.ValidationError(
                    'Repo with this Variant arch, Service, Repo family, Content format, '
                    'Content category, Name and Shadow already exists.'
                )
            except models.Repo.DoesNotExist:
                pass
        return super(RepoSerializer, self).validate(attrs)


class RepoField(serializers.RelatedField):
    """Serializer field for repository."""

    doc_format = 'Repo'
    writable_doc_format = '{"id": "int"}'
    queryset = models.Repo.objects.all()

    def to_representation(self, value):
        return RepoSerializer().to_representation(value)

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'detail': "Input [%s] must be a dict." % data})

        if data.keys() != ['id']:
            raise serializers.ValidationError({'detail': 'Only accepts {"id":"int"}'})

        repo_id = convert_str_to_int(data['id'])

        try:
            rc = models.Repo.objects.get(id=repo_id)
        except models.Repo.DoesNotExist:
            raise serializers.ValidationError({'detail': "Repo with id %s doesn't exist" % repo_id})

        return rc


class RepoFamilySerializer(StrictSerializerMixin, serializers.ModelSerializer):
    name          = serializers.CharField()
    description   = serializers.CharField()

    class Meta:
        model = models.RepoFamily
        fields = ("name", "description")


class ContentCategorySerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.ContentCategory
        fields = ('name', 'description',)


class ContentFormatSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.ContentFormat
        fields = ('name', 'pdc_endpoint', 'description',)


class ServiceSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.Service
        fields = ('name', 'description',)


class PushTargetSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    host = serializers.CharField(allow_blank=True, required=False)
    service = ChoiceSlugField(slug_field='name', queryset=models.Service.objects.all())

    class Meta:
        model = models.PushTarget
        fields = ('id', 'name', 'description', 'service', 'host')


class MultiDestinationSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    global_component = ChoiceSlugField(slug_field='name', queryset=GlobalComponent.objects.all())
    origin_repo = RepoField()
    destination_repo = RepoField()
    subscribers = ChoiceSlugField(slug_field='username', many=True, queryset=Person.objects.filter(active=True), default=[])
    active = serializers.BooleanField(default=True)

    class Meta:
        model = models.MultiDestination
        fields = (
            'id',
            'global_component',
            'origin_repo',
            'destination_repo',
            'subscribers',
            'active',
        )
