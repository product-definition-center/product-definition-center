#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.reverse import reverse

from productmd import images

from . import models
from pdc.apps.compose.models import ComposeAcceptanceTestingState
from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.repository.serializers import RepoField


class ImageFormatSerializer(serializers.SlugRelatedField):
    doc_format = " | ".join(images.SUPPORTED_IMAGE_FORMATS)

    def __init__(self):
        super(ImageFormatSerializer, self).__init__(
            slug_field='name',
            queryset=models.ImageFormat.objects.all())


class ImageTypeSerializer(serializers.SlugRelatedField):
    doc_format = " | ".join(images.SUPPORTED_IMAGE_TYPES)

    def __init__(self):
        super(ImageTypeSerializer, self).__init__(
            slug_field='name',
            queryset=models.ImageType.objects.all())


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
                    serializers.ModelSerializer):
    filename = serializers.CharField(default=DefaultFilenameGenerator())
    linked_releases = serializers.SlugRelatedField(many=True, slug_field='release_id',
                                                   queryset=models.Release.objects.all(), required=False, default=[])
    linked_composes = serializers.SlugRelatedField(read_only=True, slug_field='compose_id', many=True)
    built_for_release = serializers.SlugRelatedField(slug_field='release_id', queryset=models.Release.objects.all(),
                                                     default=None, allow_null=True)
    dependencies = DependencySerializer(required=False, default={})
    srpm_nevra = serializers.CharField(required=False, default=None)

    class Meta:
        model = models.RPM
        fields = ('id', 'name', 'version', 'epoch', 'release', 'arch', 'srpm_name',
                  'srpm_nevra', 'filename', 'linked_releases', 'linked_composes',
                  'dependencies', 'built_for_release', 'srpm_commit_hash',
                  'srpm_commit_branch')

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
    image_format    = ImageFormatSerializer()
    image_type      = ImageTypeSerializer()
    composes        = serializers.SlugRelatedField(read_only=True,
                                                   slug_field='compose_id',
                                                   many=True)

    class Meta:
        model = models.Image
        fields = ('file_name', 'image_format', 'image_type', 'disc_number',
                  'disc_count', 'arch', 'mtime', 'size', 'bootable',
                  'implant_md5', 'volume_id', 'md5', 'sha1', 'sha256',
                  'composes', 'subvariant')


def _get_fields(data, fields):
    """
    Check if all listed fields are present in data and return a dict containing
    just those.

    When something is missing, ValidationError is raised.
    """
    required_data = {}
    errors = {}
    for field in fields:
        try:
            required_data[field] = data[field]
        except KeyError:
            errors[field] = 'This field is required.'
    if errors:
        raise serializers.ValidationError(errors)
    return required_data


def _log_new_object(request, obj):
    """Create a changelog entry for new object."""
    if request and request.changeset:
        model_name = ContentType.objects.get_for_model(obj).model
        request.changeset.add(model_name,
                              obj.id,
                              'null',
                              json.dumps(obj.export()))


def _announce_new_object(request, obj, route, topic, data):
    """Enqueue a message about new object being created."""
    if request and hasattr(request, '_messagings'):
        msg = {
            'url': reverse(route, args=[obj.pk], request=request),
            'new_value': data,
        }
        request._messagings.append(('.%s.added' % topic, msg))


class RPMRelatedField(serializers.RelatedField):
    doc_format = "rpm_nevra.rpm"
    writable_doc_format = """
    {
        "name": "string",
        "epoch": "int",
        "version": "string",
        "release": "string",
        "arch": "string",
        "srpm_name": "string",
        "srpm_nevra": "string (optional, the srpm_nevra field should be empty if and only if arch is 'src')",
        "filename": "string (optional)"
    }
    """

    def to_representation(self, value):
        return unicode(value)

    def to_internal_value(self, data):
        request = self.context.get('request', None)
        if not isinstance(data, dict):
            raise serializers.ValidationError("Unsupported RPM input.")

        required_data = _get_fields(
            data, ['name', 'epoch', 'version', 'release', 'arch'])
        try:
            return models.RPM.objects.get(**required_data)
        except (models.RPM.DoesNotExist,
                models.RPM.MultipleObjectsReturned):
            serializer = RPMSerializer(data=data,
                                       context={'request': request})
            if not serializer.is_valid():
                raise serializers.ValidationError(serializer.errors)

            rpm = serializer.save()
            _log_new_object(request, rpm)
            _announce_new_object(request, rpm, 'rpms-detail', 'rpms', serializer.data)
            return rpm
        except Exception as err:
            raise serializers.ValidationError("Can not get or create RPM with your input(%s): %s." % (data, err))


class ArchiveSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = models.Archive
        fields = ('build_nvr', 'name', 'size', 'md5')


class ArchiveRelatedField(serializers.RelatedField):
    doc_format = """
    {
        "build_nvr": "string",
        "name": "string",
        "size": "int",
        "md5": "string"
    }
    """

    def to_representation(self, value):
        serializer = ArchiveSerializer(value)
        return serializer.data

    def to_internal_value(self, data):
        request = self.context.get('request', None)
        if not isinstance(data, dict):
            raise serializers.ValidationError("Unsupported Archive input.")

        required_data = _get_fields(data, ['build_nvr', 'name', 'size'])
        try:
            return models.Archive.objects.get(**required_data)
        except (models.Archive.DoesNotExist,
                models.Archive.MultipleObjectsReturned):
            serializer = ArchiveSerializer(data=data,
                                           context={'request': request})
            if not serializer.is_valid():
                raise serializers.ValidationError(serializer.errors)

            archive = serializer.save()
            _log_new_object(request, archive)
            return archive
        except Exception as err:
            raise serializers.ValidationError("Can not get or create Archive with your input(%s): %s." % (data, err))


class BuildImageSerializer(StrictSerializerMixin, serializers.HyperlinkedModelSerializer):
    image_format = ImageFormatSerializer()
    rpms = RPMRelatedField(many=True, read_only=False, queryset=models.RPM.objects.all(), required=False)
    archives = ArchiveRelatedField(many=True, read_only=False, queryset=models.Archive.objects.all(), required=False)
    releases = serializers.SlugRelatedField(many=True, slug_field='release_id', queryset=models.Release.objects.all(),
                                            required=False)

    class Meta:
        model = models.BuildImage
        fields = ('url', 'image_id', 'image_format', 'md5', 'rpms', 'archives', 'releases')


class BuildImageRTTTestsSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    format = serializers.CharField(source='image_format.name', read_only=True)
    test_result = ChoiceSlugField(slug_field='name', queryset=ComposeAcceptanceTestingState.objects.all())
    build_nvr = serializers.CharField(source='image_id', read_only=True)

    class Meta:
        model = models.BuildImage
        fields = ('id', 'build_nvr', 'format', 'test_result')


class ReleasedFilesSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    file_primary_key = serializers.IntegerField(allow_null=False)
    repo = RepoField()
    released_date = serializers.DateField(required=False)
    release_date = serializers.DateField()
    created_at = serializers.DateTimeField(required=False, read_only=True)
    updated_at = serializers.DateTimeField(required=False, read_only=True)
    zero_day_release = serializers.BooleanField(required=False, default=False)
    obsolete = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = models.ReleasedFiles
        fields = ('id', 'file_primary_key', 'repo', 'released_date',
                  'release_date', 'created_at', 'updated_at',
                  'zero_day_release', 'obsolete')

    def validate(self, data):
        if "repo" in data:
            repo_format = data["repo"].content_format
            repo_name = data["repo"].name
            if str(repo_format) != "rpm":
                raise serializers.ValidationError(
                    {'detail': 'Currently we '
                               'just support rpm type of repo, the type of %s is %s ' % (repo_name, repo_format)})

        # if there are other types support, should add codes check if the primary key in right table

        return data

    def to_representation(self, value):
        rep_data = super(ReleasedFilesSerializer, self).to_representation(value)

        if "file_primary_key" in rep_data and "repo" in rep_data:
            if rep_data["repo"]["content_format"] == "rpm":
                d = models.RPM.objects.get(id=rep_data["file_primary_key"])
                rep_data["build"] = "%s-%s-%s" % (d.srpm_name, d.version, d.arch)
                rep_data["package"] = d.srpm_name
                rep_data["file"] = d.filename

        return rep_data
