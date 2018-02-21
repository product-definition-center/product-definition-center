#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.module.models import Module, RuntimeDependency, BuildDependency
from pdc.apps.package.serializers import RPMRelatedField
from pdc.apps.package.models import RPM


# Inherit from this class so we can override the documentation variables
class RPMModuleField(RPMRelatedField):
    doc_format = '"string"'
    writable_doc_format = ('{"name": "string", "epoch": "string", "version": "string", '
                           '"release": "string", "arch": "string", "srpm_name": "string"}')


class RuntimeDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RuntimeDependency
        fields = ('dependency', 'stream')


class BuildDepSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuildDependency
        fields = ('dependency', 'stream')


class ModuleSerializerBase(StrictSerializerMixin, serializers.ModelSerializer):
    """ An abstract class for module related serializer classes to inherit from
    """
    runtime_deps = RuntimeDepSerializer(many=True, required=False)
    build_deps   = BuildDepSerializer(many=True, required=False)
    rpms         = RPMModuleField(many=True, read_only=False, queryset=RPM.objects.all(),
                                  required=False)

    def create(self, validated_data):
        runtime_deps_data = validated_data.pop('runtime_deps', [])
        build_deps_data = validated_data.pop('build_deps', [])
        rpm_data = validated_data.pop('rpms', [])

        module_obj = Module.objects.create(**validated_data)

        for dep_data in runtime_deps_data:
            RuntimeDependency.objects.create(variant=module_obj, **dep_data)

        for dep_data in build_deps_data:
            BuildDependency.objects.create(variant=module_obj, **dep_data)

        for rpm in rpm_data:
            module_obj.rpms.add(rpm)

        return module_obj


class ModuleSerializer(ModuleSerializerBase):
    # The UID is merely a combination of other fields. See the code in `validate` for more detail.
    uid = serializers.CharField(read_only=True)

    class Meta:
        model = Module
        fields = (
            'uid', 'name', 'stream', 'version', 'context', 'active', 'koji_tag', 'modulemd',
            'runtime_deps', 'build_deps', 'rpms',
        )

    def validate(self, data):
        # Set the variant_id column to the value of name for backwards compatibility
        data['variant_id'] = data['name']
        # Set the default uid to "name:stream:version:context" for convenience and to enforce
        # standards
        data['uid'] = ':'.join([data['name'], data['stream'], data['version'], data['context']])
        return data
