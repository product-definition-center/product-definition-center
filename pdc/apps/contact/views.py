#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.views.decorators.cache import never_cache
from pdc.apps.common import viewsets
from pdc.apps.common.constants import PUT_OPTIONAL_PARAM_WARNING
from .models import (Person, Maillist, ContactRole,
                     GlobalComponentContact, ReleaseComponentContact)
from .serializers import (PersonSerializer, MaillistSerializer, ContactRoleSerializer,
                          GlobalComponentContactSerializer, ReleaseComponentContactSerializer)
from .filters import (PersonFilterSet, MaillistFilterSet, ContactRoleFilterSet,
                      GlobalComponentContactFilter, ReleaseComponentContactFilter)


# Create your views here.
class PersonViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Person API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|PATCH|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """

    doc_create = """
        ### CREATE

        __Method__:
        POST

        __URL__: $LINK:person-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"username": "test", "email": "test@example.com"}' $URL:person-list$
            # output
            {"id": 1, "username": "test", "email": "test@example.com"}
    """

    doc_list = """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:person-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        ### RETRIEVE

        __Method__:
        GET

        __URL__: $LINK:person-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json" $URL:person-detail:1$
            # output
            {"id": 1, "username": "test", "email": "test@example.com"}
    """

    doc_update = """
        ### UPDATE

        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:person-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

        PUT:

            curl -X PUT -d '{"username": "new_name", "email": "new_email"}' -H "Content-Type: application/json" $URL:person-detail:1$
            # output
            {"id": 1, "username": "new_name", "email": "new_email"}

        PATCH:

            curl -X PATCH -d '{"email": "new_email"}' -H "Content-Type: application/json" $URL:person-detail:1$
            # output
            {"id": 1, "username": "name", "email": "new_email"}
    """

    doc_destroy = """
        ### DELETE

        __Method__:
        DELETE

        __URL__: $LINK:person-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:person-detail:1$
    """

    serializer_class = PersonSerializer
    queryset = Person.objects.all().order_by('id')
    filter_class = PersonFilterSet


class MaillistViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Mailing list API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|PATCH|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """

    doc_create = """
        ### CREATE

        __Method__:
        POST

        __URL__: $LINK:maillist-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"mail_name": "test", "email": "test@example.com"}' $URL:maillist-list$
            # output
            {"id": 1, "mail_name": "test", "email": "test@example.com"}
    """

    doc_list = """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:maillist-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

        With query params:

            curl -H "Content-Type: application/json"  -G $URL:maillist-list$ --data-urlencode "mail_name=test"
            # output
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "id": int,
                        "mail_name": "test",
                        "email": "test@example.com"
                    }
                ]
            }
    """

    doc_retrieve = """
        ### RETRIEVE

        __Method__:
        GET

        __URL__: $LINK:maillist-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json" $URL:maillist-detail:1$
            # output
            {"id": 1, "mail_name": "test", "email": "test@example.com"}
    """

    doc_update = """
        ### UPDATE

        __Method__: `PUT`, `PATCH`
        PUT: for full fields update
            {'mail_name': 'new_name', 'email': 'new_email'}

        PATCH: for partial update
            {'mail_name': 'new_name'}
            or
            {'email': 'new_email'}
            or
            {'mail_name': 'new_name', 'email': 'new_email'}

        __URL__: $LINK:maillist-detail:instance_pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

        PUT:

            curl -X PUT -d '{"mail_name": "new_name", "email": "new_email"}' -H "Content-Type: application/json" $URL:maillist-detail:1$
            # output
            {"id": 1, "mail_name": "new_name", "email": "new_email"}

        PATCH:

            curl -X PATCH -d '{"email": "new_email"}' -H "Content-Type: application/json" $URL:maillist-detail:1$
            # output
            {"id": 1, "mail_name": "name", "email": "new_email"}
    """

    doc_destroy = """
        ### DELETE

        __Method__:
        DELETE

        __URL__: $LINK:maillist-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:maillist-detail:1$
    """

    serializer_class = MaillistSerializer
    queryset = Maillist.objects.all().order_by('id')
    filter_class = MaillistFilterSet


class ContactRoleViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Contact Role API**, please see the
    following for more details.

    ##Test tools##

    You can use ``curl`` in terminal, with -X _method_ (GET|POST|PUT|PATCH|DELETE),
    -d _data_ (a json string). or GUI plugins for
    browsers, such as ``RESTClient``, ``RESTConsole``.
    """
    docstring_macros = PUT_OPTIONAL_PARAM_WARNING

    doc_create = """
        ### CREATE

        __Method__:
        POST

        __URL__: $LINK:contactrole-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"name": "test"}' $URL:contactrole-list$
            # output
            {"name": "test", "count_limit": 1}
    """

    doc_list = """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:contactrole-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X GET $URL:contactrole-list$
            # output
            {
                "count": 4,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "name": "qe_leader",
                        "count_limit": 1
                    },
                    {
                        "name": "qe_group",
                        "count_limit": 1
                    },
                    ...
                ]
            }

        With query params:

            curl -H "Content-Type: application/json"  -G $URL:contactrole-list$ --data-urlencode "name=test"
            # output
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "name": "test",
                        "count_limit": 1
                    }
                ]
            }
    """

    doc_retrieve = """
        ### RETRIEVE

        __Method__:
        GET

        __URL__: $LINK:contactrole-detail:role_name$

        __Response__:

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json" $URL:contactrole-detail:QE_Leader$
            # output
            {"name": "QE_Leader", "count_limit": 1}
    """

    doc_update = """
        ### UPDATE
        %(PUT_OPTIONAL_PARAM_WARNING)s

        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:contactrole-detail:role_name$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        __Response__:

        %(SERIALIZER)s

        __Example__:

        PUT:

            curl -X PUT -d '{"name": "new_name"}' -H "Content-Type: application/json" $URL:contactrole-detail:QE_Ack$
            # output
            {"name": "new_name", "count_limit": 1}

        PATCH:

            curl -X PATCH -d '{"count_limit": "unlimited"}' -H "Content-Type: application/json" $URL:contactrole-detail:QE_Ack$
            # output
            {"name": "new_name", "count_limit": "unlimited"}
    """

    doc_destroy = """
        ### DELETE

        __Method__:
        DELETE

        __URL__: $LINK:contactrole-detail:role_name$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:contactrole-detail:QE_Group$
    """

    serializer_class = ContactRoleSerializer
    queryset = ContactRole.objects.all().order_by('id')
    filter_class = ContactRoleFilterSet
    lookup_field = 'name'
    overwrite_lookup_field = False


class _BaseContactViewSet(viewsets.PDCModelViewSet):
    doc_list = """
        __Method__: `GET`

        __URL__: $LINK:%(BASENAME)s-list$

        __Query params__:

        %(FILTERS)s

        The value of `contact` filter should either be a username or mailling
        list name.

        __Response__: a paged list of following objects

        %(SERIALIZER)s
    """

    doc_retrieve = """
        __Method__: `GET`

        __URL__: $LINK:%(BASENAME)s-detail:pk$

        __Response__:

        %(SERIALIZER)s
    """

    doc_destroy = """

        __Method__: `DELETE`

        __URL__: $LINK:%(BASENAME)s-detail:pk$

        __Response__: Nothing on success.
    """

    doc_update = """

        Please note that if you change the `contact` field here, only the single
        updated relationship between contact and component will be updated.
        Specifically, no other component will be affected.

        If you update with new contact details and such contact does not exist
        yet, it will be automatically created. The specific type will be chosen
        based on whether `username` or `mail_name` was used.

        __Method__: `PUT`, `PATCH`

        __URL__: $LINK:%(BASENAME)s-detail:pk$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        %(WRITABLE_DATA_COMMENT)s

        View [list of available contact roles]($URL:contactrole-list$).

        __Response__:

        %(SERIALIZER)s
    """

    doc_create = """

        If the contact does not exist, it will be created automatically.

        __Method__: `POST`

        __URL__: $LINK:%(BASENAME)s-list$

        __Data__:

        %(WRITABLE_SERIALIZER)s

        %(WRITABLE_DATA_COMMENT)s

        Depending on whether `username` or `mail_name` is used, a person or
        mailling list will be linked to the component.

        View [list of available contact roles]($URL:contactrole-list$).

        __Response__:

        %(SERIALIZER)s
    """

    @never_cache
    def list(self, *args, **kwargs):
        return super(_BaseContactViewSet, self).list(*args, **kwargs)

    @never_cache
    def retrieve(self, *args, **kwargs):
        return super(_BaseContactViewSet, self).retrieve(*args, **kwargs)


class GlobalComponentContactViewSet(_BaseContactViewSet):

    queryset = GlobalComponentContact.objects.all().select_related().order_by('id')
    serializer_class = GlobalComponentContactSerializer
    filter_class = GlobalComponentContactFilter
    docstring_macros = {
        'BASENAME': 'globalcomponentcontacts',
        'WRITABLE_DATA_COMMENT': '',
    }


class ReleaseComponentContactViewSet(_BaseContactViewSet):

    queryset = ReleaseComponentContact.objects.all().select_related().order_by('id')
    serializer_class = ReleaseComponentContactSerializer
    filter_class = ReleaseComponentContactFilter
    docstring_macros = {
        'BASENAME': 'releasecomponentcontacts',
        'WRITABLE_DATA_COMMENT': 'The component can be alternatively specified ' +
                                 'by its id as `{"id": "int"}`.',
    }
