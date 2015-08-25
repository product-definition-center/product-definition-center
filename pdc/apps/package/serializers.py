#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from . import models
from pdc.apps.common.serializers import StrictSerializerMixin


class ReleaseRelatedField(serializers.RelatedField):
    doc_format = "Release.release_id"

    def to_representation(self, value):
        return value.release_id

    def to_internal_value(self, data):
        try:
            return self.queryset.get(release_id=data)
        except ObjectDoesNotExist:
            raise serializers.ValidationError("release with release_id %s doesn't exist." % data)
        except Exception as err:
            raise serializers.ValidationError("Can not find release with release_id (%s): %s." %
                                              (data, err))


class RPMSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    filename = serializers.CharField(required=False)
    linked_releases = ReleaseRelatedField(many=True, read_only=False, queryset=models.Release.objects.all(),
                                          required=False)
    linked_composes = serializers.SlugRelatedField(read_only=True, slug_field='compose_id', many=True)

    class Meta:
        model = models.RPM
        fields = ('id', 'name', 'version', 'epoch', 'release', 'arch', 'srpm_name', 'srpm_nevra', 'filename',
                  'linked_releases', 'linked_composes')

    def to_internal_value(self, data):
        # If filename is not present, compute one.
        if 'filename' not in data:
            data['filename'] = models.RPM.default_filename(data)
        return super(RPMSerializer, self).to_internal_value(data)


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
    releases = ReleaseRelatedField(many=True, read_only=False, queryset=models.Release.objects.all(), required=False)

    class Meta:
        model = models.BuildImage
        fields = ('url', 'image_id', 'image_format', 'md5', 'rpms', 'archives', 'releases')
