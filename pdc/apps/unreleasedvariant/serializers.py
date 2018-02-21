#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.module.models import Module
from pdc.apps.module.serializers import ModuleSerializerBase


class UnreleasedVariantSerializer(ModuleSerializerBase):
    variant_id = serializers.CharField(max_length=100, required=True, allow_null=False)
    variant_uid = serializers.CharField(source='uid')
    variant_name = serializers.CharField(source='name')
    variant_type = serializers.CharField(source='type')
    variant_version = serializers.CharField(source='stream')
    variant_release = serializers.CharField(source='version')
    variant_context = serializers.CharField(source='context', default='00000000')

    class Meta:
        model = Module
        fields = (
            'variant_id', 'variant_uid', 'variant_name', 'variant_type', 'variant_version',
            'variant_release', 'variant_context', 'koji_tag', 'modulemd', 'runtime_deps',
            'build_deps', 'active', 'rpms',
        )
