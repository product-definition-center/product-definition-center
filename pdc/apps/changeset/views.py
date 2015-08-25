#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings
from django.core.exceptions import ValidationError
from django.views.generic import ListView, DetailView

from rest_framework import viewsets, status
from rest_framework.response import Response

from pdc.apps.common.viewsets import StrictQueryParamMixin
from . import models
from .filters import ChangesetFilterSet
from .serializers import ChangesetSerializer


class ChangesetListView(ListView):
    queryset = models.Changeset.objects.all().order_by('-committed_on')
    allow_empty = True
    template_name = 'changeset_list.html'
    context_object_name = 'changeset_list'
    paginate_by = settings.ITEMS_PER_PAGE


class ChangesetDetailView(DetailView):
    model = models.Changeset
    pk_url_kwarg = "id"
    template_name = "changeset_detail.html"


class ChangesetViewSet(StrictQueryParamMixin,
                       viewsets.ReadOnlyModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Changeset API**, please see the
    following for more details.
    """

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:changeset-list$

        __QUERY Params__:

        %(FILTERS)s

        The dates for `changed_since` and `changed_until` should have one these
        formats:

            Format               | Example
            ---------------------+---------------------------
            %%Y-%%m-%%d %%H:%%M:%%S    | 2006-10-25 14:30:59
            %%Y-%%m-%%d %%H:%%M:%%S.%%f | 2006-10-25 14:30:59.000200
            %%Y-%%m-%%d %%H:%%M       | 2006-10-25 14:30
            %%Y-%%m-%%d             | 2006-10-25

        Resource names for `resource` should be specified in all lower case.

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X GET $URL:changeset-list$
            # output
            {
                "count": 84,
                "next": "$URL:changeset-list$?page=2",
                "previous": null,
                "results": [
                    {
                        {
                            "author": "xxx",
                            "committed_on": "2015-02-03T05:51:17.262Z",
                            "changes": [
                                {
                                    "resource": "person",
                                    "resource_id": 2,
                                    "old_value": "old",
                                    "new_value": "new"
                                }
                            ]
                        }

                    },
                    ...
                ]
            }

        With query params:

            curl -H "Content-Type: application/json"  -G $URL:changeset-list$ --data-urlencode "resource=test"
            # output
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                        {
                            "author": "xxx",
                            "committed_on": "2015-02-03T05:51:17.262Z",
                            "changes": [
                                {
                                    "resource": "person",
                                    "resource_id": 2,
                                    "old_value": "old",
                                    "new_value": "new"
                                }
                            ]
                        }
                ]
            }
        """
        try:
            return super(ChangesetViewSet, self).list(request, *args, **kwargs)
        except ValidationError as exc:
            msg = exc.messages if hasattr(exc, 'messages') else str(exc)
            return Response({'detail': msg},
                            status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """
        ### RETRIEVE

        __Method__:
        GET

        __URL__: $LINK:changeset-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json" $URL:changeset-detail:1$
            # output
            {"author": "xxx", "committed_on": "2015-02-03T05:51:17.262Z", "changes": [{"resource": "person", "resource_id": 2, "old_value": "old", "new_value": "new"}]}
        """
        return super(ChangesetViewSet, self).retrieve(request, *args, **kwargs)

    serializer_class = ChangesetSerializer
    queryset = models.Changeset.objects.all().order_by('-committed_on')
    filter_class = ChangesetFilterSet
