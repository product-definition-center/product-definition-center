#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from collections import OrderedDict
import logging
import re
import sys

from django.conf import settings
from django.utils.encoding import smart_text

from contrib import drf_introspection

from django.core.urlresolvers import NoReverseMatch
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.utils import formatting
from rest_framework.reverse import reverse

from pdc.apps.utils.utils import urldecode

"""
## Writing documentation in docstrings

Docstrings of each method will be available in browsable API as documentation.
These features are available to simplify writing the comments:

 * the content is formatted as Markdown
 * %(HOST_NAME)s and %(API_ROOT)s macros will be replaced by host name and URL
   fragment for API, respectively
 * %(FILTERS)s will be replaced a by a list of available query string filters
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

Responses are available in JSON format.

**NOTE:** in order to use secure HTTPS connections, you'd better to add server's certificate as trusted.

"""

URL_SPEC_RE = re.compile(r'\$(?P<type>URL|LINK):(?P<details>[^$]+)\$')


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

    def get_overview(self, view):
        if view.__class__.__name__ == 'APIRoot':
            return self.format_docstring(None, None, PDC_APIROOT_DOC)
        overview = view.__doc__ or ''
        return self.format_docstring(view, '<overview>', overview)

    def get_description(self, view, *args):
        if view.__class__.__name__ == 'APIRoot':
            return ''

        description = OrderedDict()
        for method in self.methods_mapping:
            func = getattr(view, method, None)
            docstring = func and func.__doc__ or ''
            if docstring:
                description[method] = self.format_docstring(view, method, docstring)

        return description

    def format_docstring(self, view, method, docstring):
        macros = settings.BROWSABLE_DOCUMENT_MACROS
        if view:
            macros['FILTERS'] = get_filters(view)
        string = formatting.dedent(docstring)
        formatted = string % macros
        formatted = self.substitute_urls(view, method, formatted)
        string = smart_text(formatted)
        return formatting.markup_description(string)

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


FILTERS_CACHE = {}
FILTER_DEFS = {
    'CharFilter': 'string',
    'NullableCharFilter': 'string | null',
    'BooleanFilter': 'bool',
    'ActiveReleasesFilter': 'bool',
}
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
    if view in FILTERS_CACHE:
        return FILTERS_CACHE[view]

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
            filter_type = FILTER_DEFS.get(filter.__class__.__name__, 'string')
            lookup_type = LOOKUP_TYPES.get(filter.lookup_type)
            if lookup_type:
                lookup_type = ', %s' % lookup_type
            filters.append(' * `%s` (%s%s)' % (key, filter_type, lookup_type or ''))
        elif key in filter_fields or key in extra_query_params:
            # filter defined in viewset directly; type depends on model, not easily available
            filters.append(' * `%s`' % key)
        # else filter defined somewhere else and not relevant here (e.g.
        # serializer or pagination settings).
    filters = '\n'.join(filters)
    FILTERS_CACHE[view] = filters
    return filters
