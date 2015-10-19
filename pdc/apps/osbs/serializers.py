#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.component import serializers as component_serializers
from . import models


class OSBSSerializer(StrictSerializerMixin,
                     serializers.ModelSerializer):
    component = component_serializers.ReleaseComponentField(
        read_only=True
    )
    autorebuild = serializers.NullBooleanField()

    class Meta:
        model = models.OSBSRecord
        fields = ('component', 'autorebuild')
