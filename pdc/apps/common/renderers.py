#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from collections import OrderedDict
import logging
import re
import sys
import json
import inspect

from django.conf import settings
from django.utils.encoding import smart_text

from contrib import drf_introspection

from django.db.models.fields import NOT_PROVIDED
from django.urls import NoReverseMatch
from django.core.exceptions import FieldDoesNotExist
from django_filters import NumberFilter
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.utils import formatting
from rest_framework.reverse import reverse
from rest_framework import serializers, relations, fields

from cgi import escape

from pdc.apps.utils.utils import urldecode

"""
## Writing documentation in docstrings

Docstrings of each method will be available in browsable API as documentation.
These features are available to simplify writing the comments:

 * the content is formatted as Markdown
 * %(HOST_NAME)s and %(API_ROOT)s macros will be replaced by host name and URL
   fragment for API, respectively
 * %(FILTERS)s will be replaced a by a list of available query string filters
 * %(SERIALIZER)s will be replaced by a code block with details about
   serializer
 * %(WRITABLE_SERIALIZER)s will do the same, but without read-only fields
 * $URL:route-name:arg1:arg2...$ will be replaced by absolute URL
 * $LINK:route-name:arg1:...$ will be replaced by a clickable link with
   relative URL pointing to the specified place; arguments for LINK will be
   wrapped in braces automatically

When the URL specification can not be resolve, "BAD URL" will be displayed on
the page and details about the error will be logged to the error log.
"""

SERIALIZER_DATA_INDENTATION = '    '
MODEL_FIELD_REFERENCE_RE = re.compile(r'(^[A-Z][a-zA-Z]+)\.([a-z_]+)$')


class _SerializerFieldData(object):
    def __init__(self, values):
        self.values = values


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
    return text.replace('\n', '\n' + SERIALIZER_DATA_INDENTATION)


def _serializer_field_to_string(items, container_format):
    result = ','.join(['\n' + SERIALIZER_DATA_INDENTATION + item for item in items])
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
    match = MODEL_FIELD_REFERENCE_RE.match(data)
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

    if isinstance(data, _SerializerFieldData):
        return _serializer_field_data_to_string(data, parent_fields)

    if isinstance(data, dict):
        return _serializer_field_dict_to_string(data, parent_fields)

    if isinstance(data, list):
        return _serializer_field_list_to_string(data, parent_fields)

    if isinstance(data, str) or isinstance(data, unicode):
        return _model_field_reference_to_string(data)

    return escape(json.dumps(data))


PDC_APIROOT_DOC = """
The REST APIs make it possible to programmatic access the data in Product Definition Center(a.k.a. PDC).

Create new Product, import rpms and query components with contact informations, and more.

The REST API identifies users using Token which will be generated for all authenticated users.

**Please remember to use your token as HTTP header for every requests that need authentication.**

If you want to record the reason for change, you can add Header (-H "PDC-Change-Comment: reasonforchange") in request.

Responses are available in JSON format.

**NOTE:** in order to use secure HTTPS connections, you'd better to add server's certificate as trusted.

"""

URL_SPEC_RE = re.compile(r'\$(?P<type>URL|LINK):(?P<details>[^$]+)\$')
ORDERING_STRING = """
 * `ordering` (string) Comma separated list of fields for ordering results.
    - To sort by a field in descending order, prefix its name with minus (e.g. `-name`).
    - Use double underscores for nested field names (e.g. `parent__child` for `{"parent": {"child": ...}}`).
"""
FIELDS_STRING = """

Following filters can be used to show only specific fields. This can make
response time faster. Format is list or single value
(JSON: `{"fields": ["a","b"]}` or `{"fields": "a"}`, in URL: `?fields=a&fields=b`).

 * `fields` (list | string) Fields to display (other fields will be hidden).
 * `exclude_fields`: (list | string) Fields *NOT* to display (overrules `fields`).
"""

JSON_CODE_BLOCK = '<pre><code class=serializer-data>%s</code></pre>'

DEFAULT_DESCRIPTION = {
    "list": """
        __Method__: `GET`

        __URL__: %(URL)s

        __Query params__:

        %(FILTERS)s

        __Response__:

        Paged list of following objects.

        %(SERIALIZER)s
        """,

    "retrieve": """
        __Method__: `GET`

        __URL__: %(DETAIL_URL)s

        __Response__:

        %(SERIALIZER)s
        """,

    "create": """
        __Method__: `POST`

        __URL__: %(URL)s

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """,

    "bulk_create": """
        __Method__: `POST`

        __URL__: %(URL)s

        __Data__: <code>[ <b>{Item Data}</b>, &hellip; ]</code>

        __Item Data__: %(WRITABLE_SERIALIZER)s

        __Response__:

        List of following objects.

        %(SERIALIZER)s
        """,

    "destroy": """
        __Method__: `DELETE`

        __URL__: %(DETAIL_URL)s

        __Response__:

        On success, HTTP status code is `204 NO CONTENT`.
        """,

    "bulk_destroy": """
        __Method__: `DELETE`

        __URL__: %(URL)s

        __Data__: <code>[ %(ID)s, &hellip; ]</code>

        __Response__:

        On success, HTTP status code is `204 NO CONTENT`.
        """,

    "update": """
        __Method__: `PUT`

        __URL__: %(DETAIL_URL)s

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s
        """,

    "bulk_update": """
        __Method__: `PUT`, `PATCH`

        __URL__: %(URL)s

        __Data__: <code>{ "%(ID)s": <b>{Item Data}</b>, &hellip; }</code>

        __Item Data__:

        %(WRITABLE_SERIALIZER)s

        All fields are required for `PUT` and optional for `PATCH`.

        __Response__:

        List of following objects.

        %(SERIALIZER)s
        """,

    "partial_update": """
        __Method__: `PATCH`

        __URL__: %(DETAIL_URL)s

        __Data__:

        %(WRITABLE_SERIALIZER)s

        All fields are optional.

        __Response__:

        List of following objects.

        %(SERIALIZER)s
        """,
}


def cached_by_argument_class(method):
    """
    Decorator which caches result of method call by class of the first
    argument.

    Subsequent calls with same class of the first argument just return the
    cached result.
    """
    cache = {}

    def wrapper(self, arg, *args, **kwargs):
        cache_key = arg.__class__
        if cache_key in cache:
            return cache[cache_key]

        result = method(self, arg, *args, **kwargs)
        cache[cache_key] = result
        return result

    return wrapper


class ReadOnlyBrowsableAPIRenderer(BrowsableAPIRenderer):
    template = "browsable_api/api.html"
    methods_mapping = (
        'list',
        'retrieve',
        'create',
        'bulk_create',
        'update',
        'destroy',
        'bulk_destroy',
        'partial_update',

        'bulk_update',
        # Token Auth methods
        'obtain',
        'refresh',
    )

    def get_raw_data_form(self, data, view, method, request):
        return None

    def get_rendered_html_form(self, data, view, method, request):
        return None

    def get_context(self, data, accepted_media_type, renderer_context):
        self.request = renderer_context['request']
        super_class = super(ReadOnlyBrowsableAPIRenderer, self)
        super_retval = super_class.get_context(data, accepted_media_type,
                                               renderer_context)

        if super_retval is not None:
            del super_retval['put_form']
            del super_retval['post_form']
            del super_retval['delete_form']
            del super_retval['options_form']

            del super_retval['raw_data_put_form']
            del super_retval['raw_data_post_form']
            del super_retval['raw_data_patch_form']
            del super_retval['raw_data_put_or_patch_form']

            super_retval['display_edit_forms'] = False

            super_retval['version'] = "1.0"

            view = renderer_context['view']
            super_retval['overview'] = self.get_overview(view)

        return super_retval

    @cached_by_argument_class
    def get_overview(self, view):
        if view.__class__.__name__ == 'APIRoot':
            overview = PDC_APIROOT_DOC
        else:
            overview = view.__doc__ or ''
        return self.format_description(view, None, overview)

    @cached_by_argument_class
    def get_description(self, view, *args):
        if view.__class__.__name__ == 'APIRoot':
            return ''

        description = OrderedDict()
        for method in self.methods_mapping:
            func = getattr(view, method, None)
            if func:
                docstring = inspect.cleandoc(func.__doc__ or '')

                doc_attribute = getattr(view, 'doc_' + method, None)
                if doc_attribute:
                    docstring += '\n\n' + inspect.cleandoc(doc_attribute)

                if method in DEFAULT_DESCRIPTION \
                   and '__URL__' not in docstring \
                   and '__Method__' not in docstring:
                    docstring += '\n\n' + inspect.cleandoc(DEFAULT_DESCRIPTION[method])

                description[method] = self.format_description(view, method, docstring)

        return description

    def format_description(self, view, method, description):
        macros = settings.BROWSABLE_DOCUMENT_MACROS

        if '%(FILTERS)s' in description:
            macros['FILTERS'] = get_filters(view)
            # If the API has the LIST method, show ordering field info.
            if 'list' == method and getattr(view, 'serializer_class', None) is not None:
                macros['FILTERS'] += ORDERING_STRING
                # Show fields info if applicable.
                if issubclass(view.serializer_class, drf_introspection.serializers.DynamicFieldsSerializerMixin):
                    macros['FILTERS'] += FIELDS_STRING
        if '%(SERIALIZER)s' in description:
            macros['SERIALIZER'] = get_serializer(view, include_read_only=True)
        if '%(WRITABLE_SERIALIZER)s' in description:
            macros['WRITABLE_SERIALIZER'] = get_writable_serializer(view, method)
        if '%(URL)s' in description:
            macros['URL'] = get_url(view, 'list')
        if '%(DETAIL_URL)s' in description:
            macros['DETAIL_URL'] = get_url(view, 'detail')
        if '%(ID)s' in description:
            macros['ID'] = '{%s}' % get_id_template(view)
        if hasattr(view, 'docstring_macros'):
            macros.update(view.docstring_macros)

        doc = formatting.dedent(description)
        doc = doc % macros
        doc = self.substitute_urls(view, method, doc)
        doc = smart_text(doc)
        doc = formatting.markup_description(doc)

        return doc

    def substitute_urls(self, view, method, text):
        def replace_url(match):
            type = match.groupdict()['type']
            parts = match.groupdict()['details'].split(':')
            url_name = parts[0]
            args = parts[1:]
            if type == 'LINK':
                args = ['{%s}' % arg for arg in args]
            try:
                if type == 'LINK':
                    url = reverse(url_name, args=args)
                    return '[`%s`](%s)' % (urldecode(url), url)
                return reverse(url_name, args=args, request=self.request)
            except NoReverseMatch:
                logger = logging.getLogger(__name__)
                logger.error('Bad URL specifier <%s> in %s.%s'
                             % (match.group(0), view.__class__.__name__, method),
                             exc_info=sys.exc_info())
                return 'BAD URL'
        return URL_SPEC_RE.sub(replace_url, text)


LOOKUP_TYPES = {
    'icontains': 'case insensitive, substring match',
    'contains': 'substring match',
    'iexact': 'case insensitive',
}


def get_filters(view):
    """
    For a given view set returns which query filters are available for it a
    Markdown formatted list. The list does not include query filters specified
    on serializer or query arguments used for paging.
    """
    allowed_keys = drf_introspection.get_allowed_query_params(view)
    filter_class = getattr(view, 'filter_class', None)
    filterset = filter_class() if filter_class is not None else None
    filterset_fields = filterset.filters if filterset is not None else []
    filter_fields = set(getattr(view, 'filter_fields', []))
    extra_query_params = set(getattr(view, 'extra_query_params', []))

    filters = []
    for key in sorted(allowed_keys):
        if key in filterset_fields:
            # filter defined in FilterSet
            filter = filterset_fields.get(key)
            filters.append(get_filter(key, filter))
        elif key in filter_fields or key in extra_query_params:
            # filter defined in viewset directly; type depends on model, not easily available
            filters.append(' * `%s`' % key)
        # else filter defined somewhere else and not relevant here (e.g.
        # serializer or pagination settings).

    return '\n'.join(filters)


def get_filter_option(filter, option_name):
    value = getattr(filter, option_name, '') or filter.extra.get(option_name, '')
    return value.rstrip()


def get_filter(filter_name, filter):
    filter_type = get_filter_option(filter, 'doc_format')
    if not filter_type:
        if isinstance(filter, NumberFilter):
            filter_type = 'int'
        else:
            filter_type = 'string'

    lookup_type = LOOKUP_TYPES.get(filter.lookup_expr)
    if lookup_type:
        lookup_type = ', %s' % lookup_type

    result = ' * `%s` (%s%s)' % (filter_name, filter_type, lookup_type or '')
    help_text = get_filter_option(filter, 'help_text')
    if help_text:
        result += ' ' + help_text

    return result


SERIALIZER_DEFS = {
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


def _get_type_from_str(str, default=None):
    """
    Convert docstring into object suitable for inclusion as documentation. It
    tries to parse the docstring as JSON, falling back on provided default
    value.
    """
    if str:
        try:
            return json.loads(str)
        except ValueError:
            pass
    return default if default is not None else str


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


def get_field_type(serializer, field_name, field, include_read_only):
    """
    Try to describe a field type.
    """
    if isinstance(field, (relations.ManyRelatedField, serializers.ListSerializer)):
        # Many field, recurse on child and make it a list
        if isinstance(field, relations.ManyRelatedField):
            field = field.child_relation
        else:
            field = field.child
        return [get_field_type(serializer, field_name, field, include_read_only)]
    if field.__class__.__name__ in SERIALIZER_DEFS:
        return SERIALIZER_DEFS[field.__class__.__name__]
    elif isinstance(field, serializers.SlugRelatedField):
        return _get_details_for_slug(serializer, field_name, field)
    elif isinstance(field, serializers.SerializerMethodField):
        # For method fields try to use docstring of the method.
        method_name = field.method_name or 'get_{field_name}'.format(field_name=field_name)
        method = getattr(serializer, method_name, None)
        if method:
            docstring = getattr(method, '__doc__')
            return _get_type_from_str(docstring, docstring or 'method')
    elif not include_read_only and hasattr(field, 'writable_doc_format'):
        return _get_type_from_str(field.writable_doc_format)
    elif hasattr(field, 'doc_format'):
        return _get_type_from_str(field.doc_format)
    elif isinstance(field, serializers.BaseSerializer):
        return describe_serializer(field, include_read_only)
    logger = logging.getLogger(__name__)
    logger.error('Undocumented field %s' % field)
    return 'UNKNOWN'


def get_default_value(serializer, field_name, field):
    """
    Try to get default value for a field and format it nicely.
    """
    value = field.default
    if hasattr(value, 'doc_format'):
        return (value.doc_format
                if isinstance(value.doc_format, basestring)
                else str(value.doc_format))
    if value == fields.empty:
        # Try to get default from model field.
        try:
            default = serializer.Meta.model._meta.get_field(field_name).default
            return default if default != NOT_PROVIDED else None
        except (FieldDoesNotExist, AttributeError):
            return None
    return value


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
                data[field_name] = serializer_field_data(serializer, field_name, field, include_read_only)

        return data

    if hasattr(serializer.__class__, 'doc_format'):
        return serializer.doc_format

    logger = logging.getLogger(__name__)
    logger.error('Failed to get details for serializer %s' % serializer)
    return 'data'


def serializer_field_data(serializer, field_name, field, include_read_only):
    """
    Returns key for serializer JSON data description.
    """
    key = {}
    key['value'] = serializer_field_value(serializer, field_name, field, include_read_only)

    if not include_read_only:
        tags = serializer_field_tags(serializer, field_name, field)
        if tags:
            key['tags'] = ', '.join(tags)

    description = serializer_field_help_text(serializer, field_name, field)
    if description:
        key['help'] = description

    return _SerializerFieldData(key)


def serializer_field_value(serializer, field_name, field, include_read_only):
    """
    Returns value for serializer JSON data description (recursive).
    """
    return get_field_type(serializer, field_name, field, include_read_only)


def serializer_field_tags(serializer, field_name, field):
    """
    Returns list of tags for serializer field.

    A tag can be one of: optional, nullable, default=VALUE
    """
    tags = []

    if not field.required:
        tags.append('optional')

        try:
            default = json.dumps(get_default_value(serializer, field_name, field))
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


def serializer_field_help_text(serializer, field_name, field):
    description = field_help_text(field)
    if description:
        return description

    try:
        model_field = serializer.Meta.model._meta.get_field(field_name)
        return field_help_text(model_field)
    except (AttributeError, FieldDoesNotExist):
        return ''


def field_help_text(field):
    return getattr(field, 'help_text', None) or ''


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
            return JSON_CODE_BLOCK % _serializer_data_to_string(serializer_json)
        except AssertionError:
            # Even when `get_serializer` is present, it may raise exception.
            pass

    return None


def get_id_template(view):
    if hasattr(view, 'lookup_fields'):
        lookup_fields = [field for field, _ in view.lookup_fields]
        return '}/{'.join(lookup_fields)

    if hasattr(view, 'lookup_field'):
        return view.lookup_field

    return ''


def get_url(view, detail_or_list):
    from django.urls import get_resolver
    resolver = get_resolver(None)
    viewname = '%s-%s' % (view.basename, detail_or_list)
    url_template, args = resolver.reverse_dict.getlist(viewname)[1][0][0]
    if len(args) == 1 and args[0] == 'composite_field':
        url = url_template % {'composite_field': '{%s}' % get_id_template(view)}
    else:
        url = url_template % {arg: '{%s}' % arg for arg in args}
    return '<a href="/%s">/%s</a>' % (url, url)
