#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc.apps.common.hacks import validate_model
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
