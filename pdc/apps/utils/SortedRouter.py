# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import re

from collections import OrderedDict
from django.urls import NoReverseMatch
from rest_framework import views
from rest_framework.reverse import reverse
from rest_framework.response import Response
from contrib.bulk_operations import bulk_operations

from .utils import urldecode


URL_ARG_RE = re.compile(r'\(\?P<([^>]+)>([^)]+)\)')


def get_resolver_match(request):
    try:
        return request.resolver_match
    except AttributeError:
        from django.urls import resolve
        return resolve(request.path_info)


def _get_arg_value(arg_name):
    """
    Get a possible argument value. Generally, we want to have argument name
    wrapped in braces, but when some form of primary key is expected, that
    would raise internal server error when link is clicked.
    """
    if 'pk' in arg_name:
        return '0'
    return '{%s}' % arg_name


class PDCRouter(bulk_operations.BulkRouter):
    """ Order the api url  """

    def get_api_root_view(self, api_urls=None):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        viewsets = {}
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)
            viewsets[prefix] = viewset

        class APIRoot(views.APIView):
            """
            The REST APIs make it possible to programmatic access the data in Product Definition Center(a.k.a. PDC).

            Create new Product, import rpms and query components with contact informations, and more.

            The REST API identifies users using Token which will be generated for all authenticated users.

            **Please remember to use your token as HTTP header for every requests that need authentication.**

            If you want to record the reason for change, you can add Header (-H "PDC-Change-Comment: reasonforchange") in request.

            Responses are available in JSON format.

            **NOTE:** in order to use secure HTTPS connections, you'd better to add server's certificate as trusted.

            """
            _ignore_model_permissions = True

            def get(self, request, *args, **kwargs):
                self.format = kwargs.get('format', None)
                self.request = request

                ret = OrderedDict()
                namespace = get_resolver_match(request).namespace
                sorted_api_root_dict = OrderedDict(sorted(api_root_dict.items()))
                for key, url_name in sorted_api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name
                    name = URL_ARG_RE.sub(r'{\1}', key)
                    ret[name] = None
                    self.urlargs = [_get_arg_value(arg[0]) for arg in URL_ARG_RE.findall(key)]
                    for getter in [self._get_list_url, self._get_nested_list_url, self._get_detail_url]:
                        try:
                            ret[name] = urldecode(getter(url_name, viewsets[key]))
                            break
                        except NoReverseMatch:
                            # If no known method of generating url succeeded,
                            # null will be included instead of url.
                            continue

                return Response(ret)

            def _get_list_url(self, url_name, viewset):
                return reverse(
                    url_name,
                    request=self.request,
                    format=self.format
                )

            def _get_nested_list_url(self, url_name, viewset):
                if not hasattr(viewset, 'list'):
                    raise NoReverseMatch
                return reverse(
                    url_name,
                    request=self.request,
                    args=self.urlargs,
                    format=self.format
                )

            def _get_detail_url(self, url_name, viewset):
                if not hasattr(viewset, 'retrieve'):
                    raise NoReverseMatch
                return reverse(
                    url_name[:-5] + '-detail',
                    request=self.request,
                    args=self.urlargs + ['{%s}' % viewset.lookup_field],
                    format=self.format
                )

        return APIRoot.as_view()


router = PDCRouter()
