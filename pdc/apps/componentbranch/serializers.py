#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from rest_framework import serializers
from django.conf import settings as django_settings
import re
from datetime import datetime
import six

from pdc.apps.common.fields import ChoiceSlugField
from pdc.apps.component.models import ReleaseComponentType, GlobalComponent
from pdc.apps.componentbranch.models import (
    ComponentBranch, SLA, SLAToComponentBranch)
from pdc.apps.common.serializers import StrictSerializerMixin


def is_branch_active(branch):
    """
    Checks to see if the branch is active by seeing if there are valid SLAs
    tied to the branch
    :param branch: a ComponentBranch object
    :return: a boolean
    """
    slas = branch.slas.all()
    today = datetime.utcnow().date()
    for sla in slas:
        if sla.eol >= today:
            # If the branch has at least one SLA that hasn't gone EOL, it is
            # still active
            return True

    return False


class BranchNameField(serializers.Field):
    """
    A serializer field that verifies the branch's name matches policy
    """

    doc_format = "string"

    @staticmethod
    def bad_branch_name(branch_name):
        """
        Determines if the branch name collides with the defined regex blacklist
        :param branch_name: string representing the branch name
        :return: boolean
        """
        return django_settings.COMPONENT_BRANCH_NAME_BLACKLIST_REGEX and \
            re.match(django_settings.COMPONENT_BRANCH_NAME_BLACKLIST_REGEX,
                     branch_name)

    def to_representation(self, obj):
        """
        Serializes the internal value
        :param obj: string representing the branch name
        :return: string representing the branch name
        """
        return obj

    def to_internal_value(self, data):
        """
        Takes the supplied value and ensures it conforms to branch name
        standards such as having a max length of 300 and conforming to the
        configured regex.
        :param data: the object representing the branch name
        :return: the validated branch name
        """
        if not isinstance(data, six.text_type):
            msg = ('A string was not supplied. The type was "{0}".'
                   .format(type(data).__name__))
            raise serializers.ValidationError(msg)

        if len(data) > 300:
            raise serializers.ValidationError(
                'The string must be less than 300 characters')

        if self.bad_branch_name(data):
            raise serializers.ValidationError(
                'The branch name is not allowed based on the regex "{0}"'
                .format(django_settings.COMPONENT_BRANCH_NAME_BLACKLIST_REGEX))

        return data


class SLASerializer(StrictSerializerMixin,
                    serializers.ModelSerializer):
    """
    Serializer for the SLA model
    """
    class Meta:
        model = SLA
        fields = ('id', 'name', 'description')

    def update(self, instance, validated_data):
        """
        Override the update function to not allow a user to modify the SLA name
        """
        if 'name' in validated_data and instance.name != validated_data['name']:
            error_msg = 'You may not modify the SLA\'s name due to policy'
            raise serializers.ValidationError({'name': [error_msg]})

        return super(SLASerializer, self).update(instance, validated_data)


class SLAToComponentBranchSerializerForComponentBranch(
        serializers.ModelSerializer):
    """
    A serializer for the SLAToComponentBranch model to be used in the
    ComponentBranch serializer
    """
    sla = ChoiceSlugField(slug_field='name', read_only=True)
    eol = serializers.DateField(read_only=True)

    class Meta:
        model = SLAToComponentBranch
        fields = ('id', 'sla', 'eol')


class ComponentBranchSerializer(StrictSerializerMixin,
                                serializers.ModelSerializer):
    """
    A serializer for the ComponentBranch model
    """
    name = BranchNameField()
    global_component = serializers.SlugRelatedField(
        slug_field='name', queryset=GlobalComponent.objects.all())
    type = ChoiceSlugField(
        slug_field='name', queryset=ReleaseComponentType.objects.all())
    critical_path = serializers.BooleanField(default=False)
    slas = SLAToComponentBranchSerializerForComponentBranch(
        many=True, read_only=True)
    active = serializers.SerializerMethodField('is_active')

    def is_active(self, branch):
        """
        Calls the is_branch_active function to determine if the branch is still
        active
        :param branch: a ComponentBranch object
        :return: a boolean
        """
        return is_branch_active(branch)

    class Meta:
        model = ComponentBranch
        fields = ('id', 'global_component', 'name', 'slas', 'type', 'active',
                  'critical_path')

    def update(self, instance, validated_data):
        """
        Override the update function to not allow a user to modify the branch
        name
        """
        if 'name' in validated_data and instance.name != validated_data['name']:
            raise serializers.ValidationError({
                'name': ['You may not modify the branch\'s name due to policy']
            })

        return super(ComponentBranchSerializer, self).update(
            instance, validated_data)


class ComponentBranchSerializerWithoutSLA(serializers.Serializer):
    """
    A serializer for the ComponentBranch model to be used in the
    SLAToComponentBranch serializer
    """
    id = serializers.IntegerField(read_only=True)
    name = BranchNameField()
    global_component = serializers.SlugRelatedField(
        slug_field='name', queryset=GlobalComponent.objects.all())
    type = ChoiceSlugField(
        slug_field='name', queryset=ReleaseComponentType.objects.all())
    critical_path = serializers.BooleanField(required=False)
    active = serializers.SerializerMethodField('is_active')

    def is_active(self, branch):
        """
        Calls the is_branch_active function to determine if the branch is still
        active
        :param branch: a ComponentBranch object
        :return: a boolean
        """
        return is_branch_active(branch)


class SLAToComponentBranchSerializer(StrictSerializerMixin,
                                     serializers.Serializer):
    """
    A serializer for the SLAToComponentBranch model that allows branch creation
    """
    id = serializers.IntegerField(read_only=True)
    sla = ChoiceSlugField(slug_field='name', queryset=SLA.objects.all())
    branch = ComponentBranchSerializerWithoutSLA()
    eol = serializers.DateField()

    def create(self, validated_data):
        """
        Creates the SLAToComponentBranch entry based on the serialized data
        """
        branch_component_type_name = validated_data['branch']['type']
        component_type = ReleaseComponentType.objects.filter(
            name=branch_component_type_name).first()
        if not component_type:
            error_msg = (
                'The specified ReleaseComponentType "{0}" does not exist'
                .format(branch_component_type_name))
            raise serializers.ValidationError({'branch.type': [error_msg]})

        branch_global_component_name = \
            validated_data['branch']['global_component']
        branch_global_component = GlobalComponent.objects.filter(
            name=branch_global_component_name).first()
        if not branch_global_component:
            error_msg = ('The specified GlobalComponent "{0}" does not exist'
                         .format(branch_global_component_name))
            raise serializers.ValidationError(
                {'branch.global_component': [error_msg]})

        branch_name = validated_data['branch']['name']
        branch_critical_path = validated_data['branch'].get('critical_path')
        branch = ComponentBranch.objects.filter(
            name=branch_name,
            type=component_type.id,
            global_component=branch_global_component.id).first()
        if branch:
            # The critical_path field is optional, but if it was supplied and it
            # doesn't match the found branch's critical_path field, raise an
            # error
            if branch_critical_path is not None and \
                    branch.critical_path != branch_critical_path:
                error_msg = ('The found branch\'s critical_path field did not '
                             'match the supplied value')
                raise serializers.ValidationError(
                    {'branch.critical_path': [error_msg]})
        else:
            # Set the default for this optional value when creating
            if branch_critical_path is None:
                branch_critical_path = False

            branch = ComponentBranch(
                name=branch_name,
                type=component_type,
                global_component=branch_global_component,
                critical_path=branch_critical_path,
            )

        sla_name = validated_data['sla']
        sla = SLA.objects.filter(name=sla_name).first()
        if not sla:
            error_msg = 'The specified SLA "{0}" does not exist'.format(
                sla_name)
            raise serializers.ValidationError({'sla': [error_msg]})

        if SLAToComponentBranch.objects.filter(sla=sla.id, branch=branch.id).exists():
            error_msg = (
                'The SLA "{0}" tied to the component "{1}" and branch "{2}" '
                'already exists').format(sla.name, branch.global_component.name,
                                         branch.name)
            raise serializers.ValidationError({'branch': [error_msg]})

        # This tells us if the branch object was created or not
        if branch._state.adding:
            branch.save()

        eol = validated_data['eol']
        return SLAToComponentBranch.objects.create(
            sla=sla, branch=branch, eol=eol)

    def update(self, instance, validated_data):
        """
        Updates the SLAToComponentBranch entry based on the serialized data
        """
        branch = validated_data.get('branch', {})
        branch_name = branch.get('name')
        component_type = branch.get('type')
        global_component = branch.get('global_component')
        critical_path = branch.get('critical_path', None)
        if branch:
            if instance.branch.name != branch_name \
                    or instance.branch.type != component_type \
                    or instance.branch.global_component != global_component \
                    or (critical_path is not None and
                        instance.branch.critical_path is not critical_path):
                raise serializers.ValidationError({
                    'branch': ['The branch cannot be modified using this API']})

        # TODO: Should we not allow this value to change?
        instance.sla = validated_data.get('sla', instance.sla)
        instance.eol = validated_data.get('eol', instance.eol)
        instance.save()
        return instance
