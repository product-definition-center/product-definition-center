#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib.auth import models

from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.auth.models import ResourcePermission, GroupResourcePermission


class PermissionSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    app_label = serializers.CharField(source='content_type.app_label')
    model = serializers.CharField(source='content_type.model')

    class Meta:
        model = models.Permission
        fields = ('codename', 'app_label', 'model')


class PermissionRelatedField(serializers.RelatedField):
    doc_format = "permission"

    def to_representation(self, value):
        serializer = PermissionSerializer(value)
        return serializer.data

    def to_internal_value(self, data):
        if isinstance(data, dict):
            try:
                perm = models.Permission.objects.get_by_natural_key(**data)
            except Exception as err:
                raise serializers.ValidationError("Can NOT get permission with your input(%s): %s." % (data, err))
            else:
                return perm
        else:
            raise serializers.ValidationError("Unsupported Permission input: %s" % (data))


class GroupSerializer(StrictSerializerMixin, serializers.HyperlinkedModelSerializer):

    permissions = PermissionRelatedField(many=True,
                                         queryset=models.Permission.objects.all(),
                                         read_only=False)

    class Meta:
        model = models.Group
        fields = ('url', 'name', 'permissions')


class ResourcePermissionSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    resource = serializers.CharField(source='resource.name')
    permission = serializers.CharField(source='permission.name')

    class Meta:
        model = ResourcePermission
        fields = ('resource', 'permission')


class ResourcePermissionReleatedField(serializers.RelatedField):
    def to_representation(self, instance):
        serializer = ResourcePermissionSerializer(instance)
        return serializer.data

    def to_internal_value(self, value):
        missed_set = set(['resource', 'permission']) - set(value.keys())
        if missed_set:
            raise serializers.ValidationError("Missed fields %s." % str(missed_set))

        try:
            instance = ResourcePermission.objects.get(resource__name=value['resource'],
                                                      permission__name=value['permission'])
        except ResourcePermission.DoesNotExist:
            raise serializers.ValidationError("Can't find corresponding resource permission.")
        return instance


class GroupResourcePermissionSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    group = serializers.SlugRelatedField(slug_field='name', read_only=False, queryset=models.Group.objects.all())
    resource_permission = ResourcePermissionReleatedField(queryset=ResourcePermission.objects.all())

    class Meta:
        model = GroupResourcePermission
        fields = ("id", 'resource_permission', 'group')
