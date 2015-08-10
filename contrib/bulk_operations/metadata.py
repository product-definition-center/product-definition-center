#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
Use the provided metadata generator if you wish to support OPTIONS requests on
list url of resources that support bulk operations. The only difference from
the generator provided by REST Framework is that it does not try to check
object permissions when the request would be bulk update.

To use the class, add this to your settings:

    REST_FRAMEWORK = {
        'DEFAULT_METADATA_CLASS': 'contrib.bulk_operations.metadata.BulkMetadata'
    }
"""

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework import metadata
from rest_framework.request import clone_request


class BulkMetadata(metadata.SimpleMetadata):
    """
    Simple wrapper around `SimpleMetadata` provided by REST Framework. This
    class can handle views supporting bulk operations by not checking object
    permissions on list URL.
    """

    def determine_actions(self, request, view):
        """
        For generic class based views we return information about the fields
        that are accepted for 'PUT' and 'POST' methods.

        This method expects that `get_object` may actually fail and gracefully
        handles it.

        Most of the code in this method is copied from the parent class.
        """
        actions = {}
        for method in set(['PUT', 'POST']) & set(view.allowed_methods):
            view.request = clone_request(request, method)
            try:
                # Test global permissions
                if hasattr(view, 'check_permissions'):
                    view.check_permissions(view.request)
                # Test object permissions. This will fail on list url for
                # resources supporting bulk operations. In such case
                # permissions are not checked.
                if method == 'PUT' and hasattr(view, 'get_object'):
                    try:
                        view.get_object()
                    except AssertionError:
                        pass
            except (exceptions.APIException, PermissionDenied, Http404):
                pass
            else:
                # If user has appropriate permissions for the view, include
                # appropriate metadata about the fields that should be supplied.
                serializer = view.get_serializer()
                actions[method] = self.get_serializer_info(serializer)
            finally:
                view.request = request

        return actions
