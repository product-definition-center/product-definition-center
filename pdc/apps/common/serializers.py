#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from contrib.drf_introspection.serializers import StrictSerializerMixin

from .models import Label, Arch, SigKey


class LabelSerializer(StrictSerializerMixin,
                      serializers.HyperlinkedModelSerializer):
    """
    Label Serializer
    """

    class Meta:
        model = Label
        fields = ('url', 'name', 'description')


class ArchSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Arch
        fields = ('name',)


class SigKeySerializer(StrictSerializerMixin,
                       serializers.HyperlinkedModelSerializer):
    name        = serializers.CharField(default=None)
    description = serializers.CharField(required=False, default="")

    class Meta:
        model = SigKey
        fields = ('name', 'key_id', 'description')
