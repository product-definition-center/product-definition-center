#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import re

from pdc.apps.common.hacks import validate_model
from pdc.apps.common.constants import PDC_WARNING_HEADER_NAME
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.related import OneToOneRel
from django.db.models.signals import pre_save
from django.forms.models import model_to_dict
from rest_framework.filters import OrderingFilter
from django.core.exceptions import FieldError


def connect_app_models_pre_save_signal(app, models=None):
    for model in models or app.get_models():
        pre_save.connect(validate_model, sender=model, dispatch_uid=str(model))


def group_obj_export(group_obj, fields=None):
    """
    Implement an export method for Django Group model
    """
    _fields = ['name', 'permissions'] if fields is None else fields
    return model_to_dict(group_obj, fields=_fields)


def urldecode(url):
    """Decode %7B/%7D to {}."""
    return url.replace('%7B', '{').replace('%7D', '}')


def generate_warning_header_dict(msg):
    return {PDC_WARNING_HEADER_NAME: msg}


def is_valid_regexp(in_str):
    try:
        re.compile(in_str)
        result = True
    except re.error:
        result = False
    return result


def convert_method_to_action(method):
    return {'update': 'update',
            'partial_update': 'update',
            'list': 'read',
            'retrieve': 'read',
            'create': 'create',
            'destroy': 'delete'}.get(method)


def read_permission_for_all():
    return hasattr(settings, 'ALLOW_ALL_USER_READ') and settings.ALLOW_ALL_USER_READ


def get_model_name_from_obj_or_cls(obj_or_cls):
    return ContentType.objects.get_for_model(obj_or_cls).model


def _get_field_name_and_rest(field):
    components = field.split('__', 1)
    return components[0], components[1] if len(components) == 2 else None


class RelatedNestedOrderingFilter(OrderingFilter):
    """
    Extends OrderingFilter to support ordering by fields in related models
    using Django orm '__'.

    This class is copied and changed from the patch of the github issue.
    https://github.com/encode/django-rest-framework/issues/1005#issuecomment-289555282

    This is based on rest_framework 3.2.5 because pdc-server is using
    this version.

    The patch has not been merged in the latest version yet. If pdc-server
    upgrades the rest_framework to the version which includes this patch in
    the future, this class should obsolete.
    """
    def is_valid_field(self, model, field):
        """
        Return true if the field exists within the model or there is a '__' here.
        """
        field_name, rest  = _get_field_name_and_rest(field)
        try:
            field, parent_model, direct, m2m = \
                model._meta.get_field_by_name(field_name)

            # Check if foreign key value exists
            if isinstance(field, OneToOneRel):
                return self.is_valid_field(field.related_model, rest)
            if field.rel and rest:
                return self.is_valid_field(field.rel.to, rest)
            return True
        except Exception as e:
            # There is no such field
            raise FieldError("Unknown query key: %s" % e)

    def remove_invalid_fields(self, queryset, ordering_files, view):
        """
        Rewrite the remove_invalid_fields methods and add the nested ordering
        """
        # First translate serialized field names to their source field names in model.
        serializer_fields = view.serializer_class().fields
        model_fields = []
        for field in ordering_files:
            field, rest = _get_field_name_and_rest(field)
            serializer_field = serializer_fields.get(field.lstrip('-'))
            if serializer_field and serializer_field.source:
                model_field = serializer_field.source.replace('.', '__')
                if field.startswith('-'):
                    model_field = '-' + model_field
                if rest:
                    model_field += '__' + rest
                field = model_field
            model_fields.append(field)

        return [term for term in model_fields
                if self.is_valid_field(queryset.model, term.lstrip('-'))]
