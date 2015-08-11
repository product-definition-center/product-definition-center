#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
This module provides BulkRouter that extends the registered ViewSets with bulk
operations if they are not provided yet.

To display documentation in the browsable API, it is necessary to provide a
method `bulk_op` (where `op` is any of `update`, `partial_update`, `destroy`)
on the viewset which calls `pdc.apps.common.bulk.bulk_op_impl` instead of a
parent class. Bulk create does not get its own tab in browsable API. If the
docstrings for these methods are not provided, they come with some generic
ones.
"""

from functools import wraps
from collections import OrderedDict

from rest_framework.settings import api_settings

from rest_framework import routers, status
from rest_framework.response import Response
from django.conf import settings


def _failure_response(ident, response, data=None):
    """
    Given an identifier, a response from a view and optional data, return a
    Response object that describes the error.
    """
    result = {
        'invalid_data_id': ident,
        'detail': response.data.get('detail', response.data),
    }
    if data:
        result['invalid_data'] = data
    response = Response(result, status=response.status_code)
    # This tells ChangesetMiddleware to abort the transaction.
    response.exception = True
    return response


def _safe_run(func, *args, **kwargs):
    """
    Try to run a function with given arguments. If it raises an exception, try
    to convert it to response with the exception handler. If that fails, the
    exception is re-raised.
    """
    try:
        return func(*args, **kwargs)
    except Exception, exc:
        response = api_settings.EXCEPTION_HANDLER(exc, context=kwargs)
        if response is not None:
            return response
        raise


def bulk_create_wrapper(func):
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        data = request.data
        if not isinstance(data, list):
            return func(self, request, *args, **kwargs)
        result = []
        for idx, obj in enumerate(data):
            request._full_data = obj
            response = _safe_run(func, self, request, *args, **kwargs)
            if not status.is_success(response.status_code):
                return _failure_response(idx, response, data=obj)
            # Reset object in view set.
            setattr(self, 'object', None)
            result.append(response.data)
        return Response(result, status=status.HTTP_201_CREATED)
    return wrapper


def bulk_destroy_impl(self, request, **kwargs):
    """
    It is possible to delete multiple items in one request. Use the `DELETE`
    method with the same url as for listing/creating objects. The request body
    should contain a list with identifiers for objects to be deleted. The
    identifier is usually the last part of the URL for deleting a single
    object.
    """
    if not isinstance(request.data, list):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={'detail': 'Bulk delete needs a list of identifiers.'})
    for ident in request.data:
        if not isinstance(ident, basestring) and not isinstance(ident, int):
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'detail': '"%s" is not a valid identifier.' % ident})
    self.kwargs.update(kwargs)
    for ident in OrderedDict.fromkeys(request.data):
        self.kwargs[self.lookup_field] = unicode(ident)
        response = _safe_run(self.destroy, request, **self.kwargs)
        if not status.is_success(response.status_code):
            return _failure_response(ident, response)
    return Response(status=status.HTTP_204_NO_CONTENT)


def bulk_update_impl(self, request, **kwargs):
    """
    It is possible to update multiple objects in one request. Use the `PUT` or
    `PATCH` method with the same url as for listing/creating objects. The
    request body should contain an object, where keys are identifiers of
    objects to be modified and their values use the same format as normal
    *update*.
    """
    if not isinstance(request.data, dict):
        return Response(status=status.HTTP_400_BAD_REQUEST,
                        data={'detail': 'Bulk update needs a mapping.'})
    result = {}
    self.kwargs.update(kwargs)
    orig_data = request.data
    for ident, data in orig_data.iteritems():
        self.kwargs[self.lookup_field] = unicode(ident)
        request._full_data = data
        response = _safe_run(self.update, request, **self.kwargs)
        if not status.is_success(response.status_code):
            return _failure_response(ident, response, data=data)
        result[ident] = response.data
    return Response(status=status.HTTP_200_OK, data=result)


def bulk_partial_update_impl(self, request, **kwargs):
    if not request.data:
        return Response(
            status=status.HTTP_400_BAD_REQUEST,
            data=settings.EMPTY_PATCH_ERROR_RESPONSE
        )
    self.kwargs['partial'] = True
    return self.bulk_update(request, **kwargs)


def bulk_create_dummy_impl():
    """
    It is possible to create this resource in bulk. To do so, use the same
    procedure as when creating a single instance, only the request body should
    contain a list of JSON objects. The response you get back will also contain
    a list of values which you would obtain by submitting the request data
    separately.
    """
    assert False, ('This method should never be called, it is here just so '
                   'that there is a method to attach a docstring to.')


class BulkRouter(routers.DefaultRouter):
    """
    This router provides the standard set of resources (the same as
    `DefaultRouter`). In addition to that, it allows for bulk operations on the
    collection as a whole. These are performed as a PUT/PATCH/DELETE request on
    the `{basename}-list` url. These requests are dispatched to the
    `bulk_update`, `bulk_partial_update` and `bulk_destroy` methods
    respectively.

    The bulk create does not have a dedicated method (because the URL and
    method are the same as for regular create). Currently, there is no way to
    opt-out from having bulk create added. It is however possible to define a
    method named `bulk_create` which will provide docstring to be rendered in
    browsable API. This method will never be called. If the method is missing,
    a generic documentation will be added.
    """
    def get_routes(self, viewset):
        for route in self.routes:
            if isinstance(route, routers.Route) and route.name.endswith('-list'):
                route.mapping.update({'delete': 'bulk_destroy',
                                      'put': 'bulk_update',
                                      'patch': 'bulk_partial_update'})
        return super(BulkRouter, self).get_routes(viewset)

    def register(self, prefix, viewset, base_name=None):
        if hasattr(viewset, 'create'):
            viewset.create = bulk_create_wrapper(viewset.create)
            if not hasattr(viewset, 'bulk_create'):
                viewset.bulk_create = bulk_create_dummy_impl
        if hasattr(viewset, 'destroy') and not hasattr(viewset, 'bulk_destroy'):
            viewset.bulk_destroy = bulk_destroy_impl
        if hasattr(viewset, 'update') and not hasattr(viewset, 'bulk_update'):
            viewset.bulk_update = bulk_update_impl
        if hasattr(viewset, 'partial_update') and not hasattr(viewset, 'bulk_partial_update'):
            viewset.bulk_partial_update = bulk_partial_update_impl
        super(BulkRouter, self).register(prefix, viewset, base_name)

    def get_lookup_regex(self, viewset, lookup_prefix=''):
        """
        For viewsets using the MultiLookupFieldMixin, it is necessary to
        construct the lookup_value_regex attribute here.
        """
        if hasattr(viewset, 'lookup_fields'):
            regexes = []
            for field_name, field_regex in viewset.lookup_fields:
                regexes.append('(?P<%s>%s)' % (field_name, field_regex))
            viewset.lookup_value_regex = '/'.join(regexes)

        return super(BulkRouter, self).get_lookup_regex(viewset, lookup_prefix)
