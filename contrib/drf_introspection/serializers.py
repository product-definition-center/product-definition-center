#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
This module defines two mixins intended for use with serializers.
"""

from rest_framework import serializers
from django.core.exceptions import FieldError


class IntrospectableSerializerMixin(object):
    """
    Basic mixin for a serializer that supports introspection.

    The list of fields supported by the serializer is taken from the Meta
    class. If the serializer supports processing some input data that does not
    directly correspond to declared fields, it is possible to define a class
    attribute ``extra_fields``. These fields will also be included in the list.

    If the serializer is used in multiple contexts, it may be impossible to
    specify the extra fields in the class itself. In such case, it possible to
    pass an ``extra_fields`` argument to when creating the serializer. The
    value of this argument should be a list of strings.

    Both these options can be used simultaneously.
    """
    def __init__(self, *args, **kwargs):
        self._extra_fields = set()
        if hasattr(self.__class__, 'extra_fields'):
            self._extra_fields.update(self.__class__.extra_fields)
        self._extra_fields.update(kwargs.pop('extra_fields', []))
        super(IntrospectableSerializerMixin, self).__init__(*args, **kwargs)

    def get_allowed_keys(self):
        """
        Get a set of allowed field names for given serializer.
        """
        return set(self.fields.keys()) | self._extra_fields


class StrictSerializerMixin(IntrospectableSerializerMixin):
    """
    A version of model serializer that raises a ``django.core.exceptions.FieldError``
    on deserializing data that includes unknown keys. This mixin inherits from
    the :class:`IntrospectableSerializerMixin` to be able to determine which
    fields are allowed.

    Additionally, if the input to the serializer is not a dict, a
    ``rest_framework.serializers.ValidationError`` will be raised.
    """
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError('Invalid input: must be a dict.')
        extra_fields = set(data.keys()) - self.get_allowed_keys()
        self.maybe_raise_error(extra_fields)
        return super(StrictSerializerMixin, self).to_internal_value(data)

    @staticmethod
    def maybe_raise_error(extra_fields):
        """
        Raise a ``django.core.exceptions.FieldError`` with a description
        including a list of given fields. If called with an empty set as
        argument, this function does not anything.

        This is not an instance method so that you can use it to generate error
        messages in other places, such as a view that does not use a
        serializer, but still wants to validate its input.
        """
        if extra_fields:
            raise FieldError('Unknown fields: %s.' % ', '.join('"%s"' % f for f in extra_fields))
