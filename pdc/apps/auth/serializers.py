#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib.auth import models

from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin


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
