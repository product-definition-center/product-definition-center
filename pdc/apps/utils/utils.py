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
from django.db.models.signals import pre_save
from django.forms.models import model_to_dict


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
