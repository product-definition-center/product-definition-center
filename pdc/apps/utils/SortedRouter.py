# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from collections import OrderedDict
from django.core.urlresolvers import NoReverseMatch
from rest_framework import views
from rest_framework.reverse import reverse
from rest_framework.response import Response
from contrib.bulk_operations import bulk_operations


def get_resolver_match(request):
    try:
        return request.resolver_match
    except AttributeError:
        from django.core.urlresolvers import resolve
        return resolve(request.path_info)


class PDCrouter(bulk_operations.BulkRouter):
    """ Order the api url  """

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = OrderedDict()
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

            def get(self, request, *args, **kwargs):
                ret = OrderedDict()
                namespace = get_resolver_match(request).namespace
                sorted_api_root_dict = OrderedDict(sorted(api_root_dict.items()))
                for key, url_name in sorted_api_root_dict.items():
                    if namespace:
                        url_name = namespace + ':' + url_name
                    try:
                        ret[key] = reverse(
                            url_name,
                            request=request,
                            format=kwargs.get('format', None)
                        )
                    except NoReverseMatch:
                        # Don't bail out if eg. no list routes exist, only detail routes.
                        continue

                return Response(ret)

        return APIRoot.as_view()
