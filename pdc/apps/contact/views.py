#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from pdc.apps.common import viewsets
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

    Please access this endpoint by
    [%(HOST_NAME)s/%(API_PATH)s/contacts/people/](/%(API_PATH)s/contacts/people/).
    Endpoint
    [%(HOST_NAME)s/%(API_PATH)s/persons/](/%(API_PATH)s/persons/) is deprecated.
    """

    def create(self, request, *args, **kwargs):
        """
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
        return super(PersonViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__: $LINK:person-list$

        __Query Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(PersonViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
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
        return super(PersonViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
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
        return super(PersonViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__: $LINK:person-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:person-detail:1$
        """
        return super(PersonViewSet, self).destroy(request, *args, **kwargs)

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

    Please access this endpoint by
    [%(HOST_NAME)s/%(API_PATH)s/contacts/mailing-lists/](/%(API_PATH)s/contacts/mailing-lists/).
    Endpoint
    [%(HOST_NAME)s/%(API_PATH)s/maillists/](/%(API_PATH)s/maillists/) is deprecated.
    """

    def create(self, request, *args, **kwargs):
        """
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
        return super(MaillistViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
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
        return super(MaillistViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
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
        return super(MaillistViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
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
        return super(MaillistViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__: $LINK:maillist-detail:instance_pk$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:maillist-detail:1$
        """
        return super(MaillistViewSet, self).destroy(request, *args, **kwargs)

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

    def create(self, request, *args, **kwargs):
        """
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
        return super(ContactRoleViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
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
        return super(ContactRoleViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
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
        return super(ContactRoleViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

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
        return super(ContactRoleViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__: $LINK:contactrole-detail:role_name$

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" $URL:contactrole-detail:QE_Group$
        """
        return super(ContactRoleViewSet, self).destroy(request, *args, **kwargs)

    serializer_class = ContactRoleSerializer
    queryset = ContactRole.objects.all().order_by('id')
    filter_class = ContactRoleFilterSet
    lookup_field = 'name'
    overwrite_lookup_field = False


class _BaseContactViewSet(viewsets.PDCModelViewSet):
    def list(self, *args, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:%(BASENAME)s-list$

        __Query params__:

        %(FILTERS)s

        The value of `contact` filter should either be a username or mailling
        list name.

        __Response__: a paged list of following objects

        %(SERIALIZER)s
        """
        return super(_BaseContactViewSet, self).list(*args, **kwargs)

    def retrieve(self, *args, **kwargs):
        """
        __Method__: `GET`

        __URL__: $LINK:%(BASENAME)s-detail:pk$

        __Response__:

        %(SERIALIZER)s
        """
        return super(_BaseContactViewSet, self).retrieve(*args, **kwargs)

    def destroy(self, *args, **kwargs):
        """Remove association between component and contact.

        __Method__: `DELETE`

        __URL__: $LINK:%(BASENAME)s-detail:pk$

        __Response__: Nothing on success.
        """
        return super(_BaseContactViewSet, self).destroy(*args, **kwargs)

    def update(self, *args, **kwargs):
        """Change details about a contact linked to component.

        Please not that if you change the `contact` field here, only the single
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
        return super(_BaseContactViewSet, self).update(*args, **kwargs)

    def create(self, *args, **kwargs):
        """Connect contact details with a component.

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
        return super(_BaseContactViewSet, self).create(*args, **kwargs)


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
