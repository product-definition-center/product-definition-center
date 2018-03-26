#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# https://opensource.org/licenses/MIT
#
from collections import OrderedDict
import logging
import re
import sys
import inspect

from django.conf import settings
from django.utils.encoding import smart_text

from contrib import drf_introspection

from django.urls import NoReverseMatch
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.utils import formatting
from rest_framework.reverse import reverse

from pdc.apps.utils.utils import urldecode

from .renderers_filters import get_filters
from .renderers_serializers import get_serializer, get_writable_serializer

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
