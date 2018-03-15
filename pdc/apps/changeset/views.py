#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings
from django.core.exceptions import FieldError, ValidationError
from django.views.generic import ListView, DetailView

from rest_framework import viewsets, status
from rest_framework.response import Response

from pdc.apps.auth.permissions import APIPermission
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
    PDC tracks every modification that was made through any of the API
    end-points. This provides an auditable trail of who changed what and when.

    Each request to the API creates one `Changeset`, which contains one or more
    `Change`s.

    Each `ChangeSet` carries metadata about author and date. Optionally, there
    can also be a comment, which is an arbitrary string. It is extracted from
    the `PDC-Change-Comment` HTTP header in the request.

    A `Change` has information about which database model was changed, its
    primary key and old and new value (provided as a JSON). If both the values
    are provided, the `Change` represents an update in some of the fields. If
    only new value is provided, the `Change` represents creation of new entity.
    If only old value is non-null, an entity was deleted.

    This page shows the usage of the **Changeset API**, please see the
    following for more details. The access to this data is read-only. It is
    possible to either request all changesets satisfying given criteria, or
    view detail of a particular changeset.
    """

    def list(self, request, *args, **kwargs):
        """
        __Method__:
        GET

        __URL__: $LINK:changeset-list$

        __Query Params__:

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

        The unit for duration is second.

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
                            "requested_on": "2015-02-03T05:50:49.387Z",
                            "committed_on": "2015-02-03T05:51:17.262Z",
                            "duration": "27.875",
                            "changes": [
                                {
                                    "id": 1
                                    "resource": "person",
                                    "resource_id": "2",
                                    "old_value": "old",
                                    "new_value": "new"
                                }
                            ],
                            "comment": "xxx"
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
                            "id": 1
                            "author": "xxx",
                            "requested_on": "2015-02-03T05:50:49.387Z",
                            "committed_on": "2015-02-03T05:51:17.262Z",
                            "duration": "27.875",
                            "changes": [
                                {
                                    "resource": "person",
                                    "resource_id": "2",
                                    "old_value": "old",
                                    "new_value": "new"
                                }
                            ],
                            "comment": "xxx"
                        }
                ]
            }
        """
        try:
            return super(ChangesetViewSet, self).list(request, *args, **kwargs)
        except (FieldError, ValidationError) as exc:
            msg = exc.messages if hasattr(exc, 'messages') else str(exc)
            return Response({'detail': msg},
                            status=status.HTTP_400_BAD_REQUEST)

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:changeset-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        The unit for duration is second.

        __Example__:

            curl -H "Content-Type: application/json" $URL:changeset-detail:1$
            # output
            {
                "id": 1,
                "author": "xxx",
                "requested_on": "2015-02-03T05:50:49.387Z",
                "committed_on": "2015-02-03T05:51:17.262Z",
                "duration": "27.875",
                "changes": [
                   {
                       "resource": "person",
                       "resource_id": "2",
                       "old_value": "old",
                       "new_value": "new"
                   }
                ],
                "comment": "xxx"
            }
    """

    serializer_class = ChangesetSerializer
    queryset = models.Changeset.objects.all().order_by('-committed_on')
    filter_class = ChangesetFilterSet
    permission_classes = (APIPermission,)
