#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from pdc.apps.common.serializers import StrictSerializerMixin
from pdc.apps.component.models import GlobalComponent, ReleaseComponent
from pdc.apps.component.serializers import ReleaseComponentField
from .models import (ContactRole, Person, Maillist,
                     GlobalComponentContact, ReleaseComponentContact)


class LimitField(serializers.IntegerField):
    UNLIMITED_STR = 'unlimited'
    doc_format = '"{}"|int'.format(UNLIMITED_STR)

    def __init__(self, unlimited_value, **kwargs):
        kwargs['min_value'] = 0
        super(LimitField, self).__init__(**kwargs)
        self.unlimited_value = unlimited_value

    def to_representation(self, obj):
        if obj == self.unlimited_value:
            return self.__class__.UNLIMITED_STR
        return super(LimitField, self).to_representation(obj)

    def to_internal_value(self, value):
        if value == self.__class__.UNLIMITED_STR:
            return self.unlimited_value
        return super(LimitField, self).to_internal_value(value)


class ContactRoleSerializer(StrictSerializerMixin,
                            serializers.HyperlinkedModelSerializer):
    name = serializers.SlugField()
    count_limit = LimitField(required=False, unlimited_value=ContactRole.UNLIMITED, default=1)

    class Meta:
        model = ContactRole
        fields = ('name', 'count_limit')


class PersonSerializer(StrictSerializerMixin,
                       serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Person
        fields = ('id', 'username', 'email')


class MaillistSerializer(StrictSerializerMixin,
                         serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Maillist
        fields = ('id', 'mail_name', 'email')


class ContactField(serializers.DictField):
    doc_format = '{"id": "int", "email": "email address", "username|mail_name": "string"}'
    writable_doc_format = '{"email": "email address", "username|mail_name": "string"}'

    child = serializers.CharField()
    field_to_class = {
        "username": Person,
        "mail_name": Maillist,
    }
    class_to_serializer = {
        "Person": PersonSerializer,
        "Maillist": MaillistSerializer,
    }

    def to_representation(self, value):
        leaf_value = value.as_leaf_class()
        serializer_cls = self.class_to_serializer.get(
            type(leaf_value).__name__, None)
        if serializer_cls:
            leaf_serializer = serializer_cls(exclude_fields=['url'],
                                             context=self.context)
            return leaf_serializer.to_representation(leaf_value)
        else:
            raise serializers.ValidationError("Unsupported Contact: %s" % value)

    def to_internal_value(self, data):
        v_data = super(ContactField, self).to_internal_value(data)
        for key, clazz in self.field_to_class.items():
            if key in v_data:
                contact, created = clazz.objects.get_or_create(**v_data)
                if created:
                    request = self.context.get('request', None)
                    model_name = ContentType.objects.get_for_model(contact).model
                    if request:
                        request.changeset.add(model_name,
                                              contact.id,
                                              'null',
                                              json.dumps(contact.export()))
                return contact
        raise serializers.ValidationError('Could not determine type of contact.')


class GlobalComponentContactSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    component = serializers.SlugRelatedField(slug_field='name', read_only=False,
                                             queryset=GlobalComponent.objects.all())
    role = serializers.SlugRelatedField(slug_field='name', read_only=False,
                                        queryset=ContactRole.objects.all())
    contact = ContactField()

    class Meta:
        model = GlobalComponentContact
        fields = ('id', 'component', 'role', 'contact')


class ReleaseComponentContactSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    component = ReleaseComponentField(read_only=False,
                                      queryset=ReleaseComponent.objects.all())
    role = serializers.SlugRelatedField(slug_field='name', read_only=False,
                                        queryset=ContactRole.objects.all())
    contact = ContactField()

    class Meta:
        model = ReleaseComponentContact
        fields = ('id', 'component', 'role', 'contact')
