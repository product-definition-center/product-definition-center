#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework import serializers

from contrib.drf_introspection.serializers import StrictSerializerMixin

from .models import Label, Arch, SigKey


class DynamicFieldsSerializerMixin(object):
    """
    A Serializer mixin that takes additional `fields` or `exclude_fields`
    list arguments that controls which fields should be displayed or not.

    NOTE: When given both, `exclude_fields` will be processed after `fields`.
    """

    query_params = ('fields', 'exclude_fields')

    def __init__(self, *args, **kwargs):
        # Accept kwargs in __init__, like:
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', [])
        exclude_fields = kwargs.pop('exclude_fields', [])

        # Instantiate the superclass normally
        super(DynamicFieldsSerializerMixin, self).__init__(*args, **kwargs)

        # Accept PARAMS passing from the 'request' in the serializer's context.
        if hasattr(self, 'context') and isinstance(self.context, dict):
            request = self.context.get('request', None)
            # The 'fields' and 'exclude_fields" in request should only apply to
            # top level serializer.
            top_level = self.context.get('top_level', True)
            if request and top_level:
                fields += request.query_params.getlist('fields', [])
                exclude_fields += request.query_params.getlist('exclude_fields', [])

        existing = set(self.fields.keys())
        # ignore inexistent fields input
        allowed = set(fields) & existing if fields else None
        if allowed:
            # exclude_fields *rules* fields
            if exclude_fields:
                # Drop any fields that are specified in the `exclude_fields` argument.
                allowed = allowed - set(exclude_fields)
            # Drop any fields that are not specified in the `fields` argument.
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        elif exclude_fields:
            # Drop any fields that are specified in the `exclude_fields` argument.
            for field_name in set(exclude_fields):
                self.fields.pop(field_name, None)


class LabelSerializer(StrictSerializerMixin,
                      serializers.HyperlinkedModelSerializer):
    """
    Label Serializer
    """

    class Meta:
        model = Label
        fields = ('url', 'name', 'description')


class ArchSerializer(StrictSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Arch
        fields = ('name',)


class SigKeySerializer(StrictSerializerMixin,
                       serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SigKey
        fields = ('url', 'name', 'key_id', 'description')
        extra_kwargs = {
            'url': {'lookup_field': 'key_id'}
        }
