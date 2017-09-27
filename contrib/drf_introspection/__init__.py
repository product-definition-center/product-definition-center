#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from .serializers import DynamicFieldsSerializerMixin


def get_allowed_query_params(view):
    """
    The list of allowed parameters is obtained from multiple sources:

      * filter set class
      * filter_fields attribute
      * extra_query_params attribute (which should be a list/tuple of strings)
      * paginate_by_param attribute

    The serializer can define what query parameters it uses by defining a
    `query_params` class attribute on the serializer. Note that this should
    only include the parameters that are passed via URL query string, not
    request body fields.
    """

    allowed_keys = set()

    # Take all filters from filter set.
    filter_class = getattr(view, 'filter_class', None)
    if filter_class:
        filter_set = filter_class()
        allowed_keys.update(filter_set.filters.keys())
    # Take filters if no filter set is used.
    allowed_keys.update(getattr(view.__class__, 'filter_fields', []))
    # Take extra params specified on viewset.
    allowed_keys.update(getattr(view.__class__, 'extra_query_params', []))
    # add ordering key to allowed_keys params
    allowed_keys.update(['ordering'])
    # Add pagination param.
    if hasattr(view, 'paginator'):
        page = getattr(view.paginator, 'page_query_param', None)
        if page:
            allowed_keys.add(page)
        page_size = getattr(view.paginator, 'page_size_query_param', None)
        if page_size:
            allowed_keys.add(page_size)

    # Add fields from serializer if specified.
    serializer_class = getattr(view, 'serializer_class', None)
    if serializer_class:
        allowed_keys.update(getattr(serializer_class, 'query_params', set()))

        # Add fields key if applicable.
        if issubclass(serializer_class, DynamicFieldsSerializerMixin):
            allowed_keys.add('fields')

    return allowed_keys
