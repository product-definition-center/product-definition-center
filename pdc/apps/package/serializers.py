#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from . import models
from pdc.apps.compose.models import ComposeAcceptanceTestingState
from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.common.serializers import StrictSerializerMixin, DynamicFieldsSerializerMixin


class DefaultFilenameGenerator(object):
    doc_format = '{name}-{version}-{release}.{arch}.rpm'

    def __call__(self):
        return models.RPM.default_filename(self.field.parent.initial_data)

    def set_context(self, field):
        self.field = field


class DependencySerializer(serializers.BaseSerializer):
    doc_format = '{ "recommends": ["string"], "suggests": ["string"], "obsoletes": ["string"],' \
                 '"provides": ["string"], "conflicts": ["string"], "requires": ["string"] }'

    def to_representation(self, deps):
        return deps

    def to_internal_value(self, data):
        choices = dict([(y, x) for (x, y) in models.Dependency.DEPENDENCY_TYPE_CHOICES])
        result = []
        for key in data:
            if key not in choices:
                raise serializers.ValidationError('<{}> is not a known dependency type.'.format(key))
            type = choices[key]
            if not isinstance(data[key], list):
                raise serializers.ValidationError('Value for <{}> is not a list.'.format(key))
            result.extend([self._dep_to_internal(type, key, dep) for dep in data[key]])
        return result

    def _dep_to_internal(self, type, human_type, data):
        if not isinstance(data, basestring):
            raise serializers.ValidationError('Dependency <{}> for <{}> is not a string.'.format(data, human_type))
        m = models.Dependency.DEPENDENCY_PARSER.match(data)
        if not m:
            raise serializers.ValidationError('Dependency <{}> for <{}> has bad format.'.format(data, human_type))
        groups = m.groupdict()
        return models.Dependency(name=groups['name'], type=type,
                                 comparison=groups.get('op'), version=groups.get('version'))


class RPMSerializer(StrictSerializerMixin,
                    DynamicFieldsSerializerMixin,
                    serializers.ModelSerializer):
    filename = serializers.CharField(default=DefaultFilenameGenerator())
    linked_releases = serializers.SlugRelatedField(many=True, slug_field='release_id',
                                                   queryset=models.Release.objects.all(), required=False)
    linked_composes = serializers.SlugRelatedField(read_only=True, slug_field='compose_id', many=True)
    dependencies = DependencySerializer(required=False, default={})

    class Meta:
        model = models.RPM
        fields = ('id', 'name', 'version', 'epoch', 'release', 'arch', 'srpm_name',
                  'srpm_nevra', 'filename', 'linked_releases', 'linked_composes',
                  'dependencies')

    def create(self, validated_data):
        dependencies = validated_data.pop('dependencies', [])
        instance = super(RPMSerializer, self).create(validated_data)
        for dep in dependencies:
            dep.rpm = instance
            dep.save()
        return instance

    def update(self, instance, validated_data):
        dependencies = validated_data.pop('dependencies', None)
        instance = super(RPMSerializer, self).update(instance, validated_data)
        if dependencies is not None or not self.partial:
            models.Dependency.objects.filter(rpm=instance).delete()
            for dep in dependencies or []:
                dep.rpm = instance
                dep.save()
        return instance


class ImageSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    image_format    = serializers.SlugRelatedField(slug_field='name', queryset=models.ImageFormat.objects.all())
    image_type      = serializers.SlugRelatedField(slug_field='name', queryset=models.ImageType.objects.all())
    composes        = serializers.SlugRelatedField(read_only=True,
                                                   slug_field='compose_id',
                                                   many=True)

    class Meta:
        model = models.Image
        fields = ('file_name', 'image_format', 'image_type', 'disc_number',
                  'disc_count', 'arch', 'mtime', 'size', 'bootable',
                  'implant_md5', 'volume_id', 'md5', 'sha1', 'sha256',
                  'composes')


class RPMRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        return unicode(value)

    def to_internal_value(self, data):
        request = self.context.get('request', None)
        if isinstance(data, dict):
            required_data = {}
            errors = {}
            for field in ['name', 'epoch', 'version', 'release', 'arch', 'srpm_name']:
                try:
                    required_data[field] = data[field]
                except KeyError:
                    errors[field] = 'This field is required.'
            if errors:
                raise serializers.ValidationError(errors)
            # NOTE(xchu): pop out fields not in unique_together
            required_data.pop('srpm_name')
            try:
                rpm = models.RPM.objects.get(**required_data)
            except (models.RPM.DoesNotExist,
                    models.RPM.MultipleObjectsReturned):
                serializer = RPMSerializer(data=data,
                                           context={'request': request})
                if serializer.is_valid():
                    rpm = serializer.save()
                    model_name = ContentType.objects.get_for_model(rpm).model
                    if request and request.changeset:
                        request.changeset.add(model_name,
                                              rpm.id,
                                              'null',
                                              json.dumps(rpm.export()))
                    return rpm
                else:
                    raise serializers.ValidationError(serializer.errors)
            except Exception as err:
                raise serializers.ValidationError("Can not get or create RPM with your input(%s): %s." % (data, err))
            else:
                return rpm
        else:
            raise serializers.ValidationError("Unsupported RPM input.")


class ArchiveSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.Archive
        fields = ('build_nvr', 'name', 'size', 'md5')


class ArchiveRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        serializer = ArchiveSerializer(value)
        return serializer.data

    def to_internal_value(self, data):
        request = self.context.get('request', None)

        if isinstance(data, dict):
            required_data = {}
            errors = {}
            for field in ['build_nvr', 'name', 'size', 'md5']:
                try:
                    required_data[field] = data[field]
                except KeyError:
                    errors[field] = 'This field is required.'
            if errors:
                raise serializers.ValidationError(errors)
            # NOTE(xchu): pop out fields not in unique_together
            required_data.pop('size')
            try:
                archive = models.Archive.objects.get(**required_data)
            except (models.Archive.DoesNotExist,
                    models.Archive.MultipleObjectsReturned):
                serializer = ArchiveSerializer(data=data,
                                               context={'request': request})
                if serializer.is_valid():
                    archive = serializer.save()
                    model_name = ContentType.objects.get_for_model(archive).model
                    if request and request.changeset:
                        request.changeset.add(model_name,
                                              archive.id,
                                              'null',
                                              json.dumps(archive.export()))
                    return archive
                else:
                    raise serializers.ValidationError(serializer.errors)
            except Exception as err:
                raise serializers.ValidationError("Can not get or create Archive with your input(%s): %s." % (data, err))
            else:
                return archive
        else:
            raise serializers.ValidationError("Unsupported Archive input.")


class BuildImageSerializer(StrictSerializerMixin, serializers.HyperlinkedModelSerializer):
    image_format = serializers.SlugRelatedField(slug_field='name', queryset=models.ImageFormat.objects.all())
    rpms = RPMRelatedField(many=True, read_only=False, queryset=models.RPM.objects.all(), required=False)
    archives = ArchiveRelatedField(many=True, read_only=False, queryset=models.Archive.objects.all(), required=False)
    releases = serializers.SlugRelatedField(many=True, slug_field='release_id', queryset=models.Release.objects.all(),
                                            required=False)

    class Meta:
        model = models.BuildImage
        fields = ('url', 'image_id', 'image_format', 'md5', 'rpms', 'archives', 'releases')


class BuildImageRTTTestsSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    format = serializers.CharField(source='image_format__name', read_only=True)
    test_result = ChoiceSlugField(slug_field='name', queryset=ComposeAcceptanceTestingState.objects.all())
    build_nvr = serializers.CharField(source='image_id', read_only=True)

    class Meta:
        model = models.BuildImage
        fields = ('id', 'build_nvr', 'format', 'test_result')
