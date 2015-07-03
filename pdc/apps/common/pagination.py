#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings

from rest_framework import pagination


class AutoDetectedPageNumberPagination(pagination.PageNumberPagination):
    page_size = getattr(settings, 'REST_API_PAGE_SIZE', 20)
    page_size_query_param = getattr(settings,
                                    'REST_API_PAGE_SIZE_QUERY_PARAM',
                                    'page_size')
    max_page_size = getattr(settings,
                            'REST_API_MAX_PAGE_SIZE',
                            100)

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                if int(request.query_params[self.page_size_query_param]) <= 0:
                    return None
                else:
                    return pagination._positive_int(
                        request.query_params[self.page_size_query_param],
                        strict=True,
                        cutoff=self.max_page_size
                    )
            except (KeyError, ValueError):
                pass

        return self.page_size
