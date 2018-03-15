#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc.apps.auth.permissions import APIPermission
from pdc.apps.common import viewsets
from pdc.apps.common.constants import PUT_OPTIONAL_PARAM_WARNING
from pdc.apps.release.models import Release
from pdc.apps.componentbranch.models import SLA
from .models import ReleaseSchedule
from .serializers import ReleaseScheduleSerializer
from .filters import ReleaseScheduleFilter


class ReleaseScheduleViewSet(viewsets.PDCModelViewSet):
    """
    #**Warning: This is an experimental API**#
    ##Overview##

    This page shows the usage of the **Release Schedule API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    model = ReleaseSchedule
    queryset = model.objects.all().order_by('date')
    serializer_class = ReleaseScheduleSerializer
    filter_class = ReleaseScheduleFilter
    permission_classes = (APIPermission,)
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING
    related_model_classes = (ReleaseSchedule, Release, SLA)

    doc_list = """
        __Method__:
        GET

        __URL__: $LINK:releaseschedule-list$

        __Query Params__:

        %(FILTERS)s

        __Response__:

            # paged lists
            {
                "count": int,
                "next": url,
                "previous": url,
                "results": [
                    {
                        "active": bool,
                        "date": date,
                        "id": int,
                        "release": string,
                        "release_url": string,
                        "sla": string,
                        "sla_url": string,
                    }
                    ...
            }
    """

    doc_retrieve = """
        __Method__:
        GET

        __URL__: $LINK:releaseschedule-detail:pk$

        __Response__:

            {
                "active": bool,
                "date": date,
                "id": int,
                "release": string,
                "release_url": string,
                "sla": string,
                "sla_url": string,
            }
    """

    doc_update = """
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__:

        PUT:


        PATCH:


        __URL__: $LINK:releaseschedule-detail:pk$

        __Response__:

            {
                "active": bool,
                "date": date,
                "id": int,
                "release": string,
                "release_url": string,
                "sla": string,
                "sla_url": string,
            }
    """

    doc_create = """
        __Method__:
        POST

        __URL__: $LINK:releaseschedule-list$

        __Data__:

            {
                'release': string,  # required
                'sla':     string,  # required
                'date':    date,    # required
            }

        *type*: $LINK:releaseschedule-list$

        __Response__:

            {
                "active": bool,
                "date": date,
                "id": int,
                "release": string,
                "release_url": string,
                "sla": string,
                "sla_url": string,
            }

    """

    doc_destroy = """
        __Method__:
        DELETE

        __URL__: $LINK:releaseschedule-detail:pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:releaseschedule-detail:1$
    """
