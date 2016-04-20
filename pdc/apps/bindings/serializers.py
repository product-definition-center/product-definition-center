#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
# NOTE it is important not to import any serializers module from other apps.
# Doing that could cause cyclic imports and break the application.
from django.dispatch import receiver

from rest_framework import serializers
from rest_framework.fields import SkipField

from pdc.apps.common.serializers import StrictSerializerMixin
from . import models
from pdc.apps.component import signals as releasecomponent_signals
from pdc.apps.release import signals as release_signals


class ReleaseBugzillaMappingNestedSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    product = serializers.CharField(required=False, source='bugzilla_product')

    class Meta:
        model = models.ReleaseBugzillaMapping
        fields = ('product', )


@receiver(release_signals.release_serializer_extract_data)
def bugzilla_extract_data(sender, validated_data, **kwargs):
    sender.release_bugzilla_data = validated_data.pop('releasebugzillamapping', None)


@receiver(release_signals.release_serializer_post_create)
def bugzilla_post_create(sender, release, **kwargs):
    if sender.release_bugzilla_data:
        data = sender.release_bugzilla_data
        models.ReleaseBugzillaMapping.objects.create(release=release, **data)


@receiver(release_signals.release_serializer_post_update)
def bugzilla_post_update(sender, release, **kwargs):
    if not hasattr(release, 'releasebugzillamapping'):
        bugzilla_post_create(sender, release)
        return

    explicit_remove = 'bugzilla' in sender.initial_data and sender.release_bugzilla_data is None
    implicit_remove = not sender.partial and not sender.release_bugzilla_data
    if explicit_remove or implicit_remove:
        release.releasebugzillamapping.delete()
    elif 'bugzilla_product' in (sender.release_bugzilla_data or {}):
        release.releasebugzillamapping.bugzilla_product = sender.release_bugzilla_data['bugzilla_product']
        release.releasebugzillamapping.save()


class ReleaseDistGitMappingNestedSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    branch = serializers.CharField(required=False, source='dist_git_branch')

    class Meta:
        model = models.ReleaseDistGitMapping
        fields = ('branch', )


@receiver(release_signals.release_serializer_extract_data)
def dist_git_extract_data(sender, validated_data, **kwargs):
    sender.release_distgit_data = validated_data.pop('releasedistgitmapping', None)


@receiver(release_signals.release_serializer_post_create)
def dist_git_post_create(sender, release, **kwargs):
    if sender.release_distgit_data:
        data = sender.release_distgit_data
        models.ReleaseDistGitMapping.objects.create(release=release, **data)


@receiver(release_signals.release_serializer_post_update)
def dist_git_post_update(sender, release, **kwargs):
    if not hasattr(release, 'releasedistgitmapping'):
        dist_git_post_create(sender, release)
        return

    explicit_remove = 'dist_git' in sender.initial_data and sender.release_distgit_data is None
    implicit_remove = not sender.partial and not sender.release_distgit_data
    if explicit_remove or implicit_remove:
        release.releasedistgitmapping.delete()
    elif 'dist_git_branch' in (sender.release_distgit_data or {}):
        release.releasedistgitmapping.dist_git_branch = sender.release_distgit_data['dist_git_branch']
        release.releasedistgitmapping.save()


class ReleaseComponentSRPMNameMappingNestedSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    name = serializers.CharField(required=False, source='srpm_name')

    class Meta:
        model = models.ReleaseComponentSRPMNameMapping
        fields = ('name', )

    def to_internal_value(self, data):
        if isinstance(data, dict) and 'name' in data and data['name'] is None:
            raise SkipField()
        return super(ReleaseComponentSRPMNameMappingNestedSerializer, self).to_internal_value(data)


@receiver(releasecomponent_signals.releasecomponent_serializer_extract_data)
def srpm_extract_data(sender, validated_data, **kwargs):
    sender.srpm_data = validated_data.pop('srpmnamemapping', None)


@receiver(releasecomponent_signals.releasecomponent_serializer_post_create)
def srpm_post_create(sender, release_component, **kwargs):
    if sender.srpm_data:
        data = sender.srpm_data
        models.ReleaseComponentSRPMNameMapping.objects.create(release_component=release_component, **data)


@receiver(releasecomponent_signals.releasecomponent_serializer_post_update)
def srpm_post_update(sender, release_component, **kwargs):
    if not hasattr(release_component, 'srpmnamemapping'):
        srpm_post_create(sender, release_component)
        return

    explicit_remove = 'srpm' in sender.initial_data and sender.srpm_data is None
    implicit_remove = not sender.partial and not sender.srpm_data
    if explicit_remove or implicit_remove:
        release_component.srpmnamemapping.delete()
    elif 'srpm_name' in (sender.srpm_data or {}):
        release_component.srpmnamemapping.srpm_name = sender.srpm_data['srpm_name']
        release_component.srpmnamemapping.save()


def add_field(serializer, field_name, field):
    """Add field to a serializer."""
    serializer._declared_fields[field_name] = field
    if hasattr(serializer, 'Meta') and hasattr(serializer.Meta, 'fields'):
        serializer.Meta.fields = serializer.Meta.fields + (field_name, )


def extend_release_serializer(release_serializer):
    add_field(release_serializer,
              'bugzilla',
              ReleaseBugzillaMappingNestedSerializer(source='releasebugzillamapping',
                                                     required=False,
                                                     allow_null=True,
                                                     default=None))
    add_field(release_serializer,
              'dist_git',
              ReleaseDistGitMappingNestedSerializer(source='releasedistgitmapping',
                                                    required=False,
                                                    allow_null=True,
                                                    default=None))


def extend_release_component_serializer(release_component_serializer):
    add_field(release_component_serializer,
              'srpm',
              ReleaseComponentSRPMNameMappingNestedSerializer(
                  source='srpmnamemapping',
                  required=False,
                  allow_null=True))
