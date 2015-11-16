#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers, fields
from rest_framework.reverse import reverse

from pdc.apps.common.serializers import StrictSerializerMixin, DynamicFieldsSerializerMixin
from pdc.apps.common.fields import ChoiceSlugField
from .models import Compose, OverrideRPM, ComposeAcceptanceTestingState, ComposeTree, Variant, Location, Scheme
from pdc.apps.release.models import Release
from pdc.apps.utils.utils import urldecode
from pdc.apps.repository.models import ContentCategory


class StrictManyRelatedField(serializers.ManyRelatedField):
    def get_value(self, data):
        result = super(StrictManyRelatedField, self).get_value(data)
        if not result:
            raise serializers.ValidationError(
                {self.field_name: [self.error_messages['null']]}
            )
        if result != fields.empty and not isinstance(result, list):
            raise serializers.ValidationError({self.field_name: ['Expected a list.']})
        return result


class LinkedReleasesField(serializers.SlugRelatedField):
    """
    Wrapper aroung SlugRelatedField that makes sure the input data has correct
    format.
    """
    @classmethod
    def many_init(cls, *args, **kwargs):
        child_relation = cls(**kwargs)
        return StrictManyRelatedField(*args, child_relation=child_relation)

    def to_internal_value(self, value):
        if not isinstance(value, basestring):
            raise serializers.ValidationError('Expected a string instead of <%s>.' % value)
        return super(LinkedReleasesField, self).to_internal_value(value)


class ComposeSerializer(StrictSerializerMixin,
                        DynamicFieldsSerializerMixin,
                        serializers.ModelSerializer):
    compose_type                = serializers.CharField()
    release                     = serializers.CharField()
    sigkeys                     = serializers.SerializerMethodField()
    rpm_mapping_template        = serializers.SerializerMethodField()
    acceptance_testing          = ChoiceSlugField(slug_field='name',
                                                  queryset=ComposeAcceptanceTestingState.objects.all())
    linked_releases             = LinkedReleasesField(slug_field='release_id',
                                                      many=True,
                                                      queryset=Release.objects.all())
    rtt_tested_architectures    = serializers.SerializerMethodField()

    class Meta:
        model = Compose
        fields = (
            'compose_id', 'compose_date', 'compose_type', 'compose_respin',
            'release', 'compose_label', 'deleted', 'rpm_mapping_template',
            'sigkeys', 'acceptance_testing', 'linked_releases', 'rtt_tested_architectures',
        )

    def get_rpm_mapping_template(self, obj):
        """url"""
        return urldecode(reverse(
            'composerpmmapping-detail',
            args=[obj.compose_id, '{{package}}'],
            request=self.context['request']
        ))

    def get_rtt_tested_architectures(self, obj):
        """{"variant": {"arch": "testing status"}}"""
        return obj.get_arch_testing_status()

    def get_sigkeys(self, obj):
        """["string"]"""
        return obj.sigkeys

    def validate(self, attrs):
        release = attrs.get('release') or getattr(getattr(self, 'object', None), 'release')
        if release and release in attrs.get('linked_releases', []):
            raise serializers.ValidationError('Can not link to the release for which the compose was built.')
        return attrs


class OverrideRPMSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    release = serializers.SlugRelatedField(slug_field="release_id",
                                           queryset=Release.objects.all())
    comment = serializers.CharField(default='', allow_blank=True)
    do_not_delete = serializers.BooleanField(required=False, default=False)
    include = serializers.BooleanField()

    class Meta:
        model = OverrideRPM
        fields = ('id', 'release', 'variant', 'arch', 'srpm_name', 'rpm_name',
                  'rpm_arch', 'include', 'comment', 'do_not_delete')


class ComposeTreeSerializer(StrictSerializerMixin,
                            DynamicFieldsSerializerMixin,
                            serializers.ModelSerializer):
    compose                 = serializers.SlugRelatedField(slug_field='compose_id', queryset=Compose.objects.all())
    variant                 = serializers.SlugRelatedField(slug_field='variant_uid', queryset=Variant.objects.all())
    arch                    = serializers.CharField()
    location                = ChoiceSlugField(slug_field='short', queryset=Location.objects.all())
    scheme                  = ChoiceSlugField(slug_field='name', queryset=Scheme.objects.all())
    url                     = serializers.CharField()
    synced_content          = ChoiceSlugField(slug_field='name', many=True, queryset=ContentCategory.objects.all())

    class Meta:
        model = ComposeTree
        fields = ('compose', 'variant', 'arch', 'location',
                  'scheme', 'url', 'synced_content')

    def validate(self, attrs):
        super(ComposeTreeSerializer, self).validate(attrs)
        compose = attrs.get('compose', None)
        variant = attrs.get('variant', None)
        arch = attrs.get('arch', None)
        if compose == variant.compose and arch in [i.name for i in variant.arches]:
            return attrs
        else:
            raise serializers.ValidationError('The combination with compose %s, variant %s, arch %s does not exist' %
                                              (compose, variant, arch))
