#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils import six
from django.utils.text import capfirst

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from pdc.apps.contact.models import Contact, ContactRole
from pdc.apps.contact.serializers import RoleContactSerializer
from pdc.apps.common.serializers import DynamicFieldsSerializerMixin, LabelSerializer, StrictSerializerMixin
from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.release.models import Release
from pdc.apps.common.hacks import convert_str_to_int
from .models import (GlobalComponent,
                     RoleContact,
                     ReleaseComponent,
                     Upstream,
                     BugzillaComponent,
                     ReleaseComponentGroup,
                     GroupType,
                     ReleaseComponentType,
                     ReleaseComponentRelationshipType,
                     ReleaseComponentRelationship)
from . import signals


__all__ = (
    'GlobalComponentSerializer',
    'ReleaseComponentSerializer',
    'HackedContactSerializer',
    'UpstreamSerializer',
    'BugzillaComponentSerializer',
    'GroupSerializer',
    'GroupTypeSerializer'
)


def reverse_url(request, view_name, **kwargs):
    return request.build_absolute_uri(reverse(viewname=view_name,
                                              kwargs=kwargs))


class HackedContactSerializer(RoleContactSerializer):
    """
    Could use as a view leveled serializer to encode/decode the contact data, or
    as a field in the global/release component.

    Automatically replace the url with /[global|release]-components/<instance_pk>/contacts/<pk>.
    Automatically set inherited = True when serialize release component.
    """

    def __init__(self, *args, **kwargs):
        self.inherited = kwargs.pop('inherited', False)
        self.view_name = kwargs.pop('view_name', 'globalcomponentcontact-detail')
        context = kwargs.get('context', None)
        self.instance_pk = None
        self.view = None
        # Set view/instance_pk when uses the class as a serializer.
        if context:
            self.view = context.get('view', None)
            extra_kwargs = context.get('extra_kwargs', None)
            if extra_kwargs:
                self.instance_pk = extra_kwargs.get('instance_pk', None)
        super(HackedContactSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        ret = super(HackedContactSerializer, self).to_representation(obj)
        request = self.context.get('request', None)
        url_kwargs = self.context.get('extra_kwargs', {})
        # NOTE(xchu): The `instance_pk` is needed for building a valid url,
        #             so if not provided, we should raise `KeyError`.
        instance_pk = url_kwargs['instance_pk']
        ret['url'] = reverse_url(request, self.view_name, **{
            'instance_pk': instance_pk,
            'pk': obj.pk
        })
        if self.inherited and self.view_name == 'globalcomponentcontact-detail':
            ret['inherited'] = True
        return ret

    def to_internal_value(self, data):
        # Run StrictSerializerMixin's to_internal_value() to check if extra field exists.
        super(HackedContactSerializer, self).to_internal_value(data)
        request = self.context.get('request', None)
        serializer = RoleContactSerializer(data=data,
                                           many=not isinstance(data, dict),
                                           context={'request': request})

        kwargs = {}
        kwargs['contact_role'] = data.get('contact_role')
        kwargs.update(data.get('contact'))
        try:
            contact = RoleContact.specific_objects.get(**kwargs)
        except (RoleContact.DoesNotExist, Contact.DoesNotExist, ContactRole.DoesNotExist):
            # If we can't get RoleContact in database, validate the input data and create the RoleContact.
            if serializer.is_valid(raise_exception=True):
                contact = RoleContact.specific_objects.create(**kwargs)
                if request and request.changeset:
                    model_name = ContentType.objects.get_for_model(contact).model
                    request.changeset.add(model_name,
                                          contact.id,
                                          'null',
                                          json.dumps(contact.export()))
        component_class = self.view.model

        if component_class.objects.get(pk=self.instance_pk).contacts.filter(pk=contact.pk).exists():
            model_name = six.text_type(capfirst(component_class._meta.verbose_name))
            raise serializers.ValidationError({"detail": "%s contact with this %s and Contact already exists."
                                              % (model_name, model_name)})
        else:
            return contact

    def save(self, **kwargs):
        """
        Save the deserialized object and return it.
        """

        instance_pk = self.context['extra_kwargs']['instance_pk']
        component_class = self.context['view'].model
        component = component_class.objects.get(pk=instance_pk)
        existed_contacts = component.contacts.all()

        if isinstance(self.validated_data, list):
            contacts = [self.get_object_from_db(item) for item in self.validated_data if item not in existed_contacts]

            component.contacts.add(*contacts)

            if self.validated_data['_deleted']:
                [self.delete_object(item) for item in self.validated_data['_deleted']]
        else:
            contacts = self.get_object_from_db(self.validated_data)
            component.contacts.add(contacts)

        return contacts

    def get_object_from_db(self, item):
        contact = RoleContact.objects.get(**{
            'contact_role_id': item.contact_role_id,
            'contact_id': item.contact_id
        })

        return contact

    class Meta:
        model = RoleContact
        fields = ('url', 'contact_role', 'contact')
        # In order not to run parent's validators, set validators to []
        validators = []


class HackedContactField(serializers.Field):
    """
    HackedContactField is used in GlobalComponentSerializer/ReleaseComponentSerializer insteadof HackedContactSerilizer.
    It has the ablility to get_attribute() from GlobalComponentSerializer/ReleaseComponentSerializer.
    """

    def __init__(self, view_name, *args, **kwargs):
        self.view_name = view_name
        super(HackedContactField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        serializer = HackedContactSerializer(value, many=True, context=self.context, view_name=self.view_name)
        return serializer.data

    def get_attribute(self, obj):
        """
        Get attribute from the serializer which uses this field.

        @param obj: The model object related to the serializer.
        """
        # NOTE(xchu): The `instance_pk` is needed for building a valid url,
        #             it's not provided when used as a field, so we should inject one.
        if 'extra_kwargs' not in self.context or 'instance_pk' not in self.context['extra_kwargs']:
            self.context['extra_kwargs'] = {'instance_pk': obj.pk}
        return obj.contacts.all()


class UpstreamSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Upstream
        fields = ('homepage', 'scm_type', 'scm_url')


class UpstreamRelatedField(serializers.RelatedField):
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


class GlobalComponentSerializer(DynamicFieldsSerializerMixin,
                                StrictSerializerMixin,
                                serializers.HyperlinkedModelSerializer):
    contacts = HackedContactField(required=False, read_only=False, view_name='globalcomponentcontact-detail')
    name = serializers.CharField(required=True,
                                 max_length=100)
    dist_git_path = serializers.CharField(required=False,
                                          max_length=200,
                                          allow_blank=True)
    dist_git_web_url = serializers.URLField(required=False,
                                            max_length=200)

    labels = LabelSerializer(many=True, required=False, read_only=True)
    upstream = UpstreamRelatedField(read_only=False, required=False, queryset=Upstream.objects.all())

    class Meta:
        model = GlobalComponent
        fields = ('id', 'name', 'dist_git_path', 'dist_git_web_url', 'contacts', 'labels', 'upstream')


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
                except:
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


class BugzillaComponentSerializer(DynamicFieldsSerializerMixin,
                                  StrictSerializerMixin,
                                  serializers.HyperlinkedModelSerializer):
    """
    Bugzilla Component serializer.
    """

    parent_component = serializers.CharField(required=False, max_length=200)
    subcomponents = serializers.SerializerMethodField()

    extra_fields = ['parent_pk']

    def get_subcomponents(self, obj):
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
        fields = ('name',)


class ReleaseComponentSerializer(DynamicFieldsSerializerMixin,
                                 StrictSerializerMixin,
                                 serializers.HyperlinkedModelSerializer):
    """
    ReleaseComponent Serializer
    """

    release = ReleaseField(read_only=False)
    global_component = serializers.SlugRelatedField(slug_field='name', read_only=False, queryset=GlobalComponent.objects.all())
    contacts = HackedContactField(required=False, read_only=False, view_name='releasecomponentcontact-detail')
    dist_git_branch = serializers.CharField(source='inherited_dist_git_branch', required=False)
    dist_git_web_url = serializers.URLField(required=False, max_length=200, read_only=True)
    bugzilla_component = TreeForeignKeyField(read_only=False, required=False, allow_null=True)
    brew_package = serializers.CharField(required=False)
    active = serializers.BooleanField(required=False, default=True)
    type = ChoiceSlugField(slug_field='name', queryset=ReleaseComponentType.objects.all(), required=False,
                           allow_null=True)

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

    def to_representation(self, instance):
        ret = super(ReleaseComponentSerializer, self).to_representation(instance)
        request = self.context.get("request", None)
        # Include global component contacts - PDC-184
        gcs = GlobalComponentSerializer(
            instance=instance.global_component,
            context={'request': request})
        # Exclude global component contacts whose contact_role are already in release component contacts
        gcc = gcs.data.get('contacts', [])
        contacts = ret.get('contacts', [])
        contact_role_lists = [contact['contact_role'] for contact in contacts]
        for contact in gcc:
            if contact['contact_role'] in contact_role_lists:
                continue
            contact['inherited'] = True
            contacts.append(contact)
        return ret

    def to_internal_value(self, data):
        # Raise error explictly when release and global_component are given.
        if self.instance:
            allowed_keys = self.get_allowed_keys() - set(['release', 'global_component'])
            extra_fields = set(data.keys()) - allowed_keys
            self.maybe_raise_error(extra_fields)
            data['release'] = self.instance.release
            data['global_component'] = self.instance.global_component
        return super(ReleaseComponentSerializer, self).to_internal_value(data)

    def validate_release(self, value):
        if not isinstance(value, Release):
            if isinstance(value, dict):
                release_id = value['release_id']
            else:
                release_id = value
            if release_id is None or release_id.strip() == "":
                self._errors = {'release': 'This field is required.'}
                return
            release = get_object_or_404(Release, release_id=release_id)
            if not release.is_active():
                self._errors = {'release': 'Can not create a release component with an inactive release.'}
                return
            value = release
        return value

    def validate_global_component(self, value):
        if not isinstance(value, GlobalComponent):
            global_component_name = value
            if global_component_name is None or global_component_name.strip() == "":
                self._errors = {'global_component': 'This field is required.'}
                return
            gc = get_object_or_404(GlobalComponent, name=global_component_name)
            value = gc
        return value

    def validate_name(self, value):
        if value.strip() == "":
            self._errors = {'name': 'This field is required.'}
        return value

    def validate_type(self, value):
        if not isinstance(value, ReleaseComponentType):
            if value is not None and value.strip() != "":
                value = get_object_or_404(ReleaseComponentType, name=value.strip())
            else:
                raise serializers.ValidationError("This field can't be set to null.")
        return value

    class Meta:
        model = ReleaseComponent
        fields = ('id', 'release', 'bugzilla_component', 'brew_package', 'global_component',
                  'name', 'dist_git_branch', 'dist_git_web_url', 'active',
                  'contacts', 'type')
        validators = [UniqueTogetherValidator(
            queryset=ReleaseComponent.objects.all(),
            fields=('name', 'release', 'global_component')
        )]


class GroupTypeSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    description = serializers.CharField(required=False)

    class Meta:
        model = GroupType
        fields = ('id', 'name', 'description')


class ReleaseComponentRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        result = dict()
        if value:
            result['id'] = value.id
            result['name'] = value.name
        return result

    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({'detail': "Input [%s] for ReleaseComponent must be a dict." % data})

        if set(data.keys()) not in [set(['id']), set(['release', 'global_component', 'name'])]:
            raise serializers.ValidationError(
                {'detail': "Only accept ['id'] or ['release', 'global_component', 'name']"})

        kwargs = dict()
        if 'id' in data:
            kwargs['id'] = convert_str_to_int(data.get('id'))
        else:
            kwargs['release__release_id'] = data.get('release')
            kwargs['global_component__name'] = data.get('global_component')
            kwargs['name'] = data.get('name')
        try:
            rc = ReleaseComponent.objects.get(**kwargs)
        except ReleaseComponent.DoesNotExist:
            raise serializers.ValidationError({'detail': "ReleaseComponent [%s] doesn't exist" % data})
        return rc


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
    components = ReleaseComponentRelatedField(
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
        fields = ('name',)


class RCForRelationshipRelatedField(ReleaseComponentRelatedField):
    def to_representation(self, value):
        result = dict()
        if value:
            result['id'] = value.id
            result['name'] = value.name
            result['release'] = value.release.release_id
        return result


class ReleaseComponentRelationshipSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    type = ChoiceSlugField(
        queryset=ReleaseComponentRelationshipType.objects.all(),
        slug_field='name',
        required=True,
        source='relation_type'
    )
    from_component = RCForRelationshipRelatedField(
        required=True,
        queryset=ReleaseComponent.objects.all()
    )
    to_component = RCForRelationshipRelatedField(
        required=True,
        queryset=ReleaseComponent.objects.all()
    )

    class Meta:
        model = ReleaseComponentRelationship
        fields = ('id', 'type', 'from_component', 'to_component')
