#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# https://opensource.org/licenses/MIT
#
import logging
import re
import six
import json

from django.db.models.fields import NOT_PROVIDED
from django.core.exceptions import FieldDoesNotExist
from rest_framework.utils import formatting
from rest_framework.reverse import reverse
from rest_framework import serializers, relations, fields

from cgi import escape

_SERIALIZER_DATA_INDENTATION = '    '
_MODEL_FIELD_REFERENCE_RE = re.compile(r'(^[A-Z][a-zA-Z]+)\.([a-z_]+)$')
_JSON_CODE_BLOCK = '<pre><code class=serializer-data>%s</code></pre>'
_SERIALIZER_DEFS = {
    'BooleanField': 'boolean',
    'NullBooleanField': 'boolean',
    'CharField': 'string',
    'IntegerField': 'int',
    'HyperlinkedIdentityField': 'url',
    'DateTimeField': 'datetime',
    'DateField': 'date',
    'StringRelatedField': 'string',
    'ReadOnlyField': 'data',
    'EmailField': 'email address',
    'SlugField': 'string',
    'URLField': 'url',
}


class SerializerFieldData(object):
    def __init__(self, values):
        self.values = values


def get_writable_serializer(view, method):
    serializers = get_serializer(view, include_read_only=False)

    if not serializers and method.startswith('bulk_'):
        nonbulk_method = method[5:].upper()
        return 'Same data as for %s.' % nonbulk_method

    return serializers


def get_serializer(view, include_read_only):
    """
    For given view, return a Markdown code block with JSON description of the
    serializer. If `include_read_only` is `False`, only writable fields will be
    included.
    """
    if hasattr(view, 'get_serializer'):
        try:
            serializer = view.get_serializer()
            serializer_json = describe_serializer(serializer, include_read_only)
            return _JSON_CODE_BLOCK % _serializer_data_to_string(serializer_json)
        except AssertionError:
            # Even when `get_serializer` is present, it may raise exception.
            pass

    return None


def describe_serializer(serializer, include_read_only):
    """
    Try to get description of a serializer. It tries to inspect all fields
    separately, if the serializer does not have fields, it falls back to
    `doc_format` class attribute (if present). If all fails, an error is
    logged.
    """
    if hasattr(serializer, 'get_fields'):
        data = {}
        for field_name, field in serializer.get_fields().iteritems():
            if not field.read_only or include_read_only:
                data[field_name] = _serializer_field_data(serializer, field_name, field, include_read_only)

        return data

    if hasattr(serializer.__class__, 'doc_format'):
        return serializer.doc_format

    logger = logging.getLogger(__name__)
    logger.error('Failed to get details for serializer %s' % serializer)
    return 'data'


def _serializer_field_attribute_to_string(css_class, field_data):
    return '<span class="serializer-field-%s">%s</span>' % (css_class, field_data)


def _serializer_field_link(text, field_name, base_name):
    return '<a href="%s#field-%s">%s</a>' % (reverse(base_name + '-list'), field_name, text)


def _serializer_field_data_to_string(field_data, parent_fields):
    value = field_data.values.pop('value')
    value = _serializer_data_to_string(value, parent_fields)
    value = _serializer_field_attribute_to_string('value', value)

    detail_items = []
    for key in ['tags', 'help']:
        if key in field_data.values:
            detail_items.append(_serializer_field_attribute_to_string(key, field_data.values[key]))

    if detail_items:
        value += ' ' + _serializer_field_attribute_to_string('details', ' '.join(detail_items))

    return value


def _indented_text(text):
    return text.replace('\n', '\n' + _SERIALIZER_DATA_INDENTATION)


def _serializer_field_to_string(items, container_format):
    result = ','.join(['\n' + _SERIALIZER_DATA_INDENTATION + item for item in items])
    return container_format % (result + '\n')


def _serializer_field_dict_to_string(field, parent_fields):
    items = []
    for field_name, field_data in sorted(field.iteritems()):
        key = _serializer_field_attribute_to_string('name', '"%s"' % field_name)
        parent_fields.append(field_name)
        value = _serializer_data_to_string(field_data, parent_fields)
        field_id = 'field-' + '__'.join(parent_fields)
        parent_fields.pop()
        html = '<span class="serializer-field" id="%s">%s: %s</span>' % (field_id, key, _indented_text(value))
        items.append(html)

    return _serializer_field_to_string(items, '{%s}')


def _serializer_field_list_to_string(field, parent_fields):
    items = []
    for field_data in field:
        value = _serializer_data_to_string(field_data, parent_fields)
        items.append(_indented_text(value))

    if len(items) == 1:
        return '[ %s, &hellip; ]' % items[0]

    return _serializer_field_to_string(items, '[%s]')


def _model_field_reference_to_string(data):
    match = _MODEL_FIELD_REFERENCE_RE.match(data)
    if match is not None:
        model_name = match.group(1)
        field_name = match.group(2)

        for model_class, base_name in _models_and_base_names():
            if model_class.__name__ == model_name:
                return _serializer_field_link(data, field_name, base_name)

    return data


def _serializer_data_to_string(data, parent_fields=None):
    if parent_fields is None:
        parent_fields = []

    if isinstance(data, SerializerFieldData):
        return _serializer_field_data_to_string(data, parent_fields)

    if isinstance(data, dict):
        return _serializer_field_dict_to_string(data, parent_fields)

    if isinstance(data, list):
        return _serializer_field_list_to_string(data, parent_fields)

    if isinstance(data, six.string_types):
        return _model_field_reference_to_string(data)

    return escape(json.dumps(data))


def _get_type_from_docstring(value, default=None):
    """
    Convert docstring into object suitable for inclusion as documentation. It
    tries to parse the docstring as JSON, falling back on provided default
    value.
    """
    if value:
        try:
            return json.loads(value)
        except ValueError:
            return formatting.dedent(str(value))

    if default is not None:
        return default

    return None


def _models_and_base_names():
    from pdc.apps.utils.SortedRouter import router
    for _, viewset, base_name in router.registry:
        serializer_class = getattr(viewset, 'serializer_class', None)
        meta = getattr(serializer_class, 'Meta', None)
        serializer_model_class = getattr(meta, 'model', None)
        if serializer_model_class:
            yield serializer_model_class, base_name


def _get_details_for_slug(serializer, field_name, field):
    """
    For slug field, we ideally want to get Model.field format. However, in some
    cases getting the model name is not possible, and only field name is
    displayed.

    Tries to guess the model from "source" or "queryset" attributes.
    """
    if getattr(field, 'source', None) is not None and field.source.endswith('_set'):
        model_name = field.source[:-4].lower()
        for model_class, base_name in _models_and_base_names():
            if model_class.__name__.lower() == model_name:
                return '%s.%s' % (model_class.__name__, field.slug_field)

    if getattr(field, 'queryset', None) is not None:
        model = field.queryset.model
        if model:
            return '%s.%s' % (model.__name__, field.slug_field)

    return field.slug_field


def _get_field_type(serializer, field_name, field, include_read_only):
    """
    Try to describe a field type.
    """
    if isinstance(field, (relations.ManyRelatedField, serializers.ListSerializer)):
        # Many field, recurse on child and make it a list
        if isinstance(field, relations.ManyRelatedField):
            field = field.child_relation
        else:
            field = field.child
        return [_get_field_type(serializer, field_name, field, include_read_only)]
    if field.__class__.__name__ in _SERIALIZER_DEFS:
        return _SERIALIZER_DEFS[field.__class__.__name__]
    elif isinstance(field, serializers.SlugRelatedField):
        return _get_details_for_slug(serializer, field_name, field)
    elif isinstance(field, serializers.SerializerMethodField):
        # For method fields try to use docstring of the method.
        method_name = field.method_name or 'get_{field_name}'.format(field_name=field_name)
        method = getattr(serializer, method_name, None)
        if method:
            docstring = getattr(method, '__doc__')
            return _get_type_from_docstring(docstring, docstring or 'method')
    elif not include_read_only and hasattr(field, 'writable_doc_format'):
        return _get_type_from_docstring(field.writable_doc_format)
    elif hasattr(field, 'doc_format'):
        return _get_type_from_docstring(field.doc_format)
    elif isinstance(field, serializers.BaseSerializer):
        return describe_serializer(field, include_read_only)
    logger = logging.getLogger(__name__)
    logger.error('Undocumented field %s' % field)
    return 'UNKNOWN'


def _get_default_value(serializer, field_name, field):
    """
    Try to get default value for a field and format it nicely.
    """
    value = field.default
    if hasattr(value, 'doc_format'):
        return _get_type_from_docstring(value.doc_format)
    if value == fields.empty:
        # Try to get default from model field.
        try:
            default = serializer.Meta.model._meta.get_field(field_name).default
            return default if default != NOT_PROVIDED else None
        except (FieldDoesNotExist, AttributeError):
            return None
    return value


def _serializer_field_data(serializer, field_name, field, include_read_only):
    """
    Returns key for serializer JSON data description.
    """
    key = {}
    key['value'] = _serializer_field_value(serializer, field_name, field, include_read_only)

    if not include_read_only:
        tags = _serializer_field_tags(serializer, field_name, field)
        if tags:
            key['tags'] = ', '.join(tags)

    if include_read_only and field.allow_null:
        key['tags'] = 'nullable'

    description = _serializer_field_help_text(serializer, field_name, field)
    if description:
        key['help'] = description

    return SerializerFieldData(key)


def _serializer_field_value(serializer, field_name, field, include_read_only):
    """
    Returns value for serializer JSON data description (recursive).
    """
    return _get_field_type(serializer, field_name, field, include_read_only)


def _serializer_field_tags(serializer, field_name, field):
    """
    Returns list of tags for serializer field.

    A tag can be one of: optional, nullable, default=VALUE
    """
    tags = []

    if not field.required:
        tags.append('optional')

        try:
            default = json.dumps(_get_default_value(serializer, field_name, field))
            if not (default is None and field.allow_null):
                tags.append('default=%s' % escape(default))
        except TypeError:
            pass

    if field.allow_null:
        tags.append('nullable')

    try:
        model_field = serializer.Meta.model._meta.get_field(field_name)
        if model_field.unique:
            tags.append('unique')
    except (AttributeError, FieldDoesNotExist):
        pass

    return tags


def _serializer_field_help_text(serializer, field_name, field):
    description = _field_help_text(field)
    if description:
        return description

    try:
        model_field = serializer.Meta.model._meta.get_field(field_name)
        return _field_help_text(model_field)
    except (AttributeError, FieldDoesNotExist):
        return ''


def _field_help_text(field):
    return getattr(field, 'help_text', None) or ''
