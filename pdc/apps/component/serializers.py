#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from rest_framework import serializers

from pdc.apps.common.serializers import LabelSerializer, StrictSerializerMixin
from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.release.models import Release
from pdc.apps.common.hacks import convert_str_to_int
from .models import (GlobalComponent,
                     ReleaseComponent,
                     Upstream,
                     BugzillaComponent,
                     ReleaseComponentGroup,
                     GroupType,
                     ReleaseComponentType,
                     ReleaseComponentRelationshipType,
                     ReleaseComponentRelationship)
from . import signals


def reverse_url(request, view_name, **kwargs):
    return request.build_absolute_uri(reverse(viewname=view_name,
                                              kwargs=kwargs))


class UpstreamSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Upstream
        fields = ('homepage', 'scm_type', 'scm_url')


class UpstreamRelatedField(serializers.RelatedField):
    doc_format = """
        {
            "homepage": "url",
            "scm_type": "string",
            "scm_url": "url"
        }
    """

    def to_representation(self, value):
        serializer = UpstreamSerializer(value)
        return serializer.data

    def to_internal_value(self, value):
        request = self.context.get('request', None)
        if isinstance(value, dict):
            try:
                upstream = Upstream.objects.get(**value)
            except Upstream.DoesNotExist:
                serializer = UpstreamSerializer(data=value, many=False, context={'request': request})
                if serializer.is_valid(raise_exception=True):
                    upstream = serializer.save()
                    model_name = ContentType.objects.get_for_model(upstream).model
                    if request and request.changeset:
                        request.changeset.add(model_name,
                                              upstream.id,
                                              'null',
                                              json.dumps(upstream.export()))
                    return upstream
                else:
                    self._errors = serializer._errors
            except Exception as err:
                raise serializers.ValidationError("Can not get or create Upstream with the input(%s): %s." % (value, err))
            else:
                return upstream
        else:
            raise serializers.ValidationError("Unsupported upstream input.")


class GlobalComponentSerializer(StrictSerializerMixin,
                                serializers.HyperlinkedModelSerializer):
    name = serializers.CharField(required=True,
                                 max_length=200)
    dist_git_path = serializers.CharField(required=False,
                                          max_length=200,
                                          allow_blank=True)
    dist_git_web_url = serializers.URLField(required=False,
                                            max_length=200)

    labels = LabelSerializer(many=True, required=False, read_only=True)
    upstream = UpstreamRelatedField(read_only=False, required=False, allow_null=True, queryset=Upstream.objects.all())

    class Meta:
        model = GlobalComponent
        fields = ('id', 'name', 'dist_git_path', 'dist_git_web_url', 'labels', 'upstream')


class TreeForeignKeyField(serializers.Field):

    def to_representation(self, value):
        request = self.context.get("request", None)
        serializer = BugzillaComponentSerializer(value, context={'request': request, 'top_level': False})
        return serializer.data

    def to_internal_value(self, data):
        if data.strip() == "":
            raise serializers.ValidationError({'bugzilla_component': 'This field is required.'})
        else:
            components = data.strip("/").split("/")
            len_components = len(components)
            bc = None
            # Only Bugzilla component name exists, parent component name will be considered as None.
            if len_components == 1:
                try:
                    bc = BugzillaComponent.objects.get(name=components[0], parent_component=None)
                except Exception:
                    raise serializers.ValidationError({'bugzilla_component': ("Bugzilla component with name %s does not exist."
                                                                              % data)})
            # Not only bugzilla Component, but also its ancestors exist.
            if len_components > 1:
                z = zip(components, components[1:])
                root_bc_name, bc_name = z[0]
                qs = BugzillaComponent.objects.filter(name=bc_name, parent_component__name=root_bc_name)
                for _, bc_name in z[1:]:
                    qs = BugzillaComponent.objects.filter(name=bc_name, parent_component__in=qs)
                if not qs:
                    raise serializers.ValidationError({'bugzilla_component': ("Bugzilla component with name %s does not exist."
                                                                              % data)})
                if len(qs) > 1:
                    raise serializers.ValidationError({'bugzilla_component': ("Duplicate Bugzilla component with name %s exists."
                                                                              % data)})
                if qs:
                    bc = qs[0]
            return bc


class BugzillaComponentSerializer(StrictSerializerMixin,
                                  serializers.HyperlinkedModelSerializer):
    """
    Bugzilla Component serializer.
    """

    parent_component = serializers.CharField(required=False, max_length=200)
    subcomponents = serializers.SerializerMethodField()

    extra_fields = ['parent_pk']

    def get_subcomponents(self, obj):
        """["string"]"""
        return obj.get_subcomponents()

    class Meta:
        model = BugzillaComponent
        fields = ('id', 'name', 'parent_component', 'subcomponents')


class ReleaseField(serializers.SlugRelatedField):
    def __init__(self, **kwargs):
        super(ReleaseField, self).__init__(slug_field='release_id',
                                           queryset=Release.objects.all(),
                                           **kwargs)

    def to_representation(self, value):
        return {
            'release_id': value.release_id,
            'active': value.active
        }


class ReleaseComponentTypeSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = ReleaseComponentType
        fields = ('name', 'has_osbs')


class ReleaseComponentSerializer(StrictSerializerMixin,
                                 serializers.HyperlinkedModelSerializer):
    """
    ReleaseComponent Serializer
    """

    release = ReleaseField(read_only=False)
    global_component = serializers.SlugRelatedField(slug_field='name', read_only=False, queryset=GlobalComponent.objects.all())
    dist_git_branch = serializers.CharField(source='inherited_dist_git_branch', required=False)
    dist_git_web_url = serializers.URLField(required=False, max_length=200, read_only=True)
    bugzilla_component = TreeForeignKeyField(read_only=False, required=False, allow_null=True)
    brew_package = serializers.CharField(required=False)
    active = serializers.BooleanField(required=False, default=True)
    type = ChoiceSlugField(slug_field='name', queryset=ReleaseComponentType.objects.all(), required=False, default=lambda: ReleaseComponentType.objects.get(name='rpm'))

    def update(self, instance, validated_data):
        signals.releasecomponent_serializer_extract_data.send(sender=self, validated_data=validated_data)
        instance = super(ReleaseComponentSerializer, self).update(instance, validated_data)
        signals.releasecomponent_serializer_post_update.send(sender=self, release_component=instance)
        if hasattr(instance, 'pk'):
            # reload to make sure changes in mapping are reflected
            instance = ReleaseComponent.objects.get(pk=instance.pk)
        # from view's doc, for ReleaseComponent,
        # PUT and PATCH update works the same as each other except `name` is required when PUT update,
        # so there will be not setattr here.
        return instance

    def create(self, validated_data):
        signals.releasecomponent_serializer_extract_data.send(sender=self, validated_data=validated_data)
        instance = super(ReleaseComponentSerializer, self).create(validated_data)
        signals.releasecomponent_serializer_post_create.send(sender=self, release_component=instance)
        return instance

    def to_internal_value(self, data):
        # Raise error explictly when release are given.
        if self.instance:
            allowed_keys = self.get_allowed_keys() - set(['release'])
            extra_fields = set(data.keys()) - allowed_keys
            self.maybe_raise_error(extra_fields)
            data['release'] = self.instance.release
            data['global_component'] = data.get('global_component', self.instance.global_component)
        return super(ReleaseComponentSerializer, self).to_internal_value(data)

    def validate_release(self, value):
        if not value.is_active():
            raise serializers.ValidationError('Can not create a release component with an inactive release.')
        return value

    class Meta:
        model = ReleaseComponent
        fields = ('id', 'release', 'bugzilla_component', 'brew_package', 'global_component',
                  'name', 'dist_git_branch', 'dist_git_web_url', 'active', 'type')


class GroupTypeSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    description = serializers.CharField(required=False, default='')

    class Meta:
        model = GroupType
        fields = ('id', 'name', 'description')


class ReleaseComponentField(serializers.RelatedField):
    """Serializer field for including release component details."""
    doc_format = '{"id": "int", "name": "string", "release": "Release.release_id"}'
    writable_doc_format = '{"release": "Release.release_id", "name": "string"}'

    def to_representation(self, value):
        result = dict()
        if value:
            result['id'] = value.id
            result['name'] = value.name
            result['release'] = value.release.release_id
        return result

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'detail': "Input [%s] for ReleaseComponent must be a dict." % data})

        if set(data.keys()) not in [set(['id']), set(['release', 'name'])]:
            raise serializers.ValidationError(
                {'detail': "Only accept ['id'] or ['release', 'name']"})

        kwargs = dict()
        if 'id' in data:
            kwargs['id'] = convert_str_to_int(data.get('id'))
        else:
            kwargs['release__release_id'] = data.get('release')
            kwargs['name'] = data.get('name')
        try:
            rc = ReleaseComponent.objects.get(**kwargs)
        except ReleaseComponent.DoesNotExist:
            raise serializers.ValidationError({'detail': "ReleaseComponent [%s] doesn't exist" % data})
        return rc


class ReleaseComponentWithoutReleaseField(ReleaseComponentField):
    """Exactly the same as ReleaseComponentField, but does not include release."""
    doc_format = '{"id": "int", "name": "string"}'

    def to_representation(self, value):
        result = dict()
        if value:
            result['id'] = value.id
            result['name'] = value.name
        return result


class GroupSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    group_type = serializers.SlugRelatedField(
        queryset=GroupType.objects.all(),
        slug_field='name',
        required=True
    )
    release = serializers.SlugRelatedField(
        queryset=Release.objects.all(),
        slug_field='release_id',
        required=True
    )
    description = serializers.CharField(required=True)
    components = ReleaseComponentWithoutReleaseField(
        required=False,
        many=True,
        queryset=ReleaseComponent.objects.all()
    )

    def validate(self, value):
        # # POST
        if not self.instance:
            components = value.get('components', [])
            release = value.get('release')
        # PUT or PATCH
        else:
            components = value.get('components', self.instance.components.all())
            release = value.get('release', self.instance.release)

        for component in components:
                if component.release != release:
                    raise serializers.ValidationError({
                        'detail': 'Not allow to group release_component[%s] <release[%s]> with other release[%s].'
                                  % (component.name, component.release.release_id, release.release_id)})
        return value

    class Meta:
        model = ReleaseComponentGroup
        fields = ('id', 'group_type', 'description', 'release', 'components')


class RCRelationshipTypeSerializer(StrictSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = ReleaseComponentRelationshipType
        fields = ('id', 'name')


class ReleaseComponentRelationshipSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    type = ChoiceSlugField(
        queryset=ReleaseComponentRelationshipType.objects.all(),
        slug_field='name',
        required=True,
        source='relation_type'
    )
    from_component = ReleaseComponentField(
        required=True,
        queryset=ReleaseComponent.objects.all()
    )
    to_component = ReleaseComponentField(
        required=True,
        queryset=ReleaseComponent.objects.all()
    )

    class Meta:
        model = ReleaseComponentRelationship
        fields = ('id', 'type', 'from_component', 'to_component')
