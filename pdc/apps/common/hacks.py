# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import re

from django.db import connection
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import serializers

from productmd import composeinfo, images, rpms
from pkg_resources import parse_version


def composeinfo_from_str(data):
    ci = composeinfo.ComposeInfo()
    try:
        ci.deserialize(data)
    except KeyError as e:
        raise serializers.ValidationError(
            {'detail': 'Error parsing composeinfo.',
             'reason': 'Missing key %s' % e.message}
        )
    except Exception as e:
        raise serializers.ValidationError(
            {'detail': 'Error parsing composeinfo.',
             'reason': str(e)}
        )
    return ci


def rpms_from_str(data):
    rm = rpms.Rpms()
    rm.deserialize(data)
    return rm


def images_from_str(data):
    im = images.Images()
    im.deserialize(data)
    return im


def add_returning(sql):
    """
    Add SQL clause required to return id of inserted item if the backend needs
    it. The suffix is created only once and then cached.
    """
    if not hasattr(add_returning, '_returning'):
        add_returning._returning = ""
        r_fmt = connection.ops.return_insert_id()
        if r_fmt:
            add_returning._returning = " " + r_fmt[0] % "id"
    return sql + add_returning._returning


def bool_from_native(value):
    """Convert value to bool."""
    if value in ('false', 'f', 'False', '0'):
        return False
    return bool(value)


def convert_str_to_bool(value, name=None):
    """
    Try to strictly convert a string value to boolean or raise ValidationError.
    """
    if value in (True, 'true', 't', 'True', '1'):
        return True
    if value in (False, 'false', 'f', 'False', '0'):
        return False
    ident = ' of %s' % name if name else ''
    raise serializers.ValidationError('Value [%s]%s is not a boolean' % (value, ident))


def as_instance(arg, type, name=None):
    """Return arg if it is an instance of type, otherwise raise ValidationError."""
    if not isinstance(arg, type):
        ident = '%s: ' % name if name else ''
        raise ValidationError('%s"%s" is not a %s' % (ident, arg, type.__name__))
    return arg


def as_list(arg, name=None):
    return as_instance(arg, list, name)


def as_dict(arg, name=None):
    return as_instance(arg, dict, name)


def convert_str_to_int(value, name=None):
    """
    Convert a string value to int or raise ValidationError.
    """
    try:
        value = int(value)
    except:
        ident = ' of %s' % name if name else ''
        raise ValidationError('Value [%s]%s is not an integer' % (value, ident))
    else:
        return value


def validate_model(sender, **kwargs):
    if "raw" in kwargs and not kwargs["raw"]:
        kwargs["instance"].full_clean()


def srpm_name_to_component_names(srpm_name):
    if settings.WITH_BINDINGS:
        from pdc.apps.bindings import models as binding_models
        return binding_models.ReleaseComponentSRPMNameMapping.get_component_names_by_srpm_name(srpm_name)
    else:
        return [srpm_name]


def parse_epoch_version(version):
    """
    Wrapper around `pkg_resources.parse_version` that can handle epochs
    delimited by colon as is customary for RPMs.
    """
    if re.match(r'^\d+:', version):
        version = re.sub(r'^(\d+):', r'\1!', version)
    return parse_version(version)
