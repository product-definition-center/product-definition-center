#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin
from .models import Changeset, Change


class ChangeSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    resource = serializers.CharField(source='target_class')
    resource_id = serializers.CharField(source='target_id')

    class Meta:
        model = Change
        fields = ('resource', 'resource_id', 'old_value', 'new_value')


class ChangesetSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    changes = ChangeSerializer(source='change_set', many=True, read_only=True)

    class Meta:
        model = Changeset
        fields = ('id', 'author', 'requested_on', 'committed_on', 'duration', 'changes', 'comment')
