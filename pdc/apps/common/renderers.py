#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from collections import OrderedDict

from django.conf import settings
from django.utils.encoding import smart_text

from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.utils import formatting


PDC_APIROOT_DOC = """
The REST APIs make it possible to programmatic access the data in Product Definition Center(a.k.a. PDC).

Create new Product, import rpms and query components with contact informations, and more.

The REST API identifies users using Token which will be generated for all authenticated users.

**Please remember to use your token as HTTP header for every requests that need authentication.**

Responses are available in JSON format.

**NOTE:** in order to use secure HTTPS connections, you'd better to add server's certificate as trusted.

"""


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
            return self.format_docstring(PDC_APIROOT_DOC)
        overview = view.__doc__ or ''
        return self.format_docstring(overview)

    def get_description(self, view):
        if view.__class__.__name__ == 'APIRoot':
            return ''

        description = OrderedDict()
        for method in self.methods_mapping:
            func = getattr(view, method, None)
            docstring = func and func.__doc__ or ''
            if docstring:
                description[method] = self.format_docstring(docstring)

        return description

    def format_docstring(self, docstring):
        formatted = docstring % settings.BROWSABLE_DOCUMENT_MACROS
        string = formatting.dedent(smart_text(formatted))
        return formatting.markup_description(string)
