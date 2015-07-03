#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_text

from rest_framework import serializers


class ChoiceSlugField(serializers.SlugRelatedField):
    """
    Wrapper around SlugRelatedField that includes a list of possible values in
    error message should the given value not match anything.

    The only functional difference from SlugRelatedField is handling
    ObjectDoesNotExist exception and the corresponding error message.
    """

    default_error_messages = {
        'does_not_exist': "'%s' is not allowed value. Use one of %s.",
    }

    def to_internal_value(self, data):
        if self.queryset is None:
            raise Exception('Writable related fields must include a `queryset` argument')
        try:
            return self.queryset.get(**{self.slug_field: data})
        except ObjectDoesNotExist:
            opts = ["'" + getattr(obj, self.slug_field) + "'"
                    for obj in self.queryset.all()]
            raise serializers.ValidationError(self.error_messages['does_not_exist'] %
                                              (smart_text(data), ', '.join(opts)))
        except (TypeError, ValueError):
            msg = self.error_messages['invalid']
            raise serializers.ValidationError(msg)
