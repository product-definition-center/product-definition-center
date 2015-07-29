#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db.models import Q

from pdc.apps.common import viewsets
from .models import Person, Maillist, ContactRole, Contact, RoleContact
from .serializers import (PersonSerializer, MaillistSerializer,
                          ContactRoleSerializer, RoleContactSerializer)
from .filters import PersonFilterSet, MaillistFilterSet, ContactRoleFilterSet


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

    def create(self, request, *args, **kwargs):
        """
        ### CREATE

        __Method__:
        POST

        __URL__:
        /persons/

        __Data__:

            {
                'username':    string,         # required
                'email':       email_address   # required
            }
        __Response__:

            {
                "id": int,
                "username": string,
                "email": email_address
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"username": "test", "email": "test@example.com"}' %(HOST_NAME)s/%(API_PATH)s/persons/
            # output
            {"id": 1, "username": "test", "email": "test@example.com"}
        """
        return super(PersonViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__:
        /persons/

        __QUERY Params__:

            username     # optional
            email        # optional

        __Response__:

            # paged lists
            {
                "count": 284,
                "next": "%(HOST_NAME)s/%(API_PATH)s/persons/?page=2",
                "previous": null,
                "results": [
                    {
                        "id": int,
                        "username": string,
                        "email": email_address
                    },
                    ...
            }
        """
        return super(PersonViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        ### RETRIEVE

        __Method__:
        GET

        __URL__:
        /persons/{instance_pk}

        __Response__:

            {
                "id": int,
                "username": string,
                "email": email_address
            }

        __Example__:

            curl -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/persons/1/
            # output
            {"id": 1, "username": "test", "email": "test@example.com"}
        """
        return super(PersonViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__:

        PUT: for full fields update
            {'username': 'new_name', 'email': 'new_email'}

        PATCH: for partial update
            {'username': 'new_name'}
            or
            {'email': 'new_email'}
            or
            {'username': 'new_name', 'email': 'new_email'}

        __URL__:
        /persons/{instance_pk}

        __Response__:

            {
                "id": int,
                "username": string,
                "email": email_address
            }

        __Example__:

        PUT:

            curl -X PUT -d '{"username": "new_name", "email": "new_email"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/persons/1/
            # output
            {"id": 1, "username": "new_name", "email": "new_email"}

        PATCH:

            curl -X PATCH -d '{"email": "new_email"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/persons/1/
            # output
            {"id": 1, "username": "name", "email": "new_email"}
        """
        return super(PersonViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__:
        /persons/{instance_pk}

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/persons/1/
        """
        return super(PersonViewSet, self).destroy(request, *args, **kwargs)

    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    filter_class = PersonFilterSet


class MaillistViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **Maillist API**, please see the
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

        __URL__:
        /maillists/

        __Data__:

            {
                'mail_name':   string,         # required
                'email':       email_address   # required
            }
        __Response__:

            {
                "id": int,
                "mail_name": string,
                "email": email_address
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"mail_name": "test", "email": "test@example.com"}' %(HOST_NAME)s/%(API_PATH)s/maillists/
            # output
            {"id": 1, "mail_name": "test", "email": "test@example.com"}
        """
        return super(MaillistViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__:
        /maillists/

        __QUERY Params__:

            mail_name    # optional
            email        # optional

        __Response__:

            # paged lists
            {
                "count": 28,
                "next": "%(HOST_NAME)s/%(API_PATH)s/maillist/?page=2",
                "previous": null,
                "results": [
                    {
                        "id": int,
                        "mail_name": string,
                        "email": string
                    },
                    ...
            }

        __Example__:

        With query params:

            curl -H "Content-Type: application/json"  -G %(HOST_NAME)s/%(API_PATH)s/maillists/ --data-urlencode "mail_name=test"
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

        __URL__:
        /maillists/{instance_pk}

        __Response__:

            {
                "id": int,
                "mail_name": string,
                "email": email_address
            }

        __Example__:

            curl -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/maillists/1/
            # output
            {"id": 1, "mail_name": "test", "email": "test@example.com"}
        """
        return super(MaillistViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__:
        PUT: for full fields update
            {'mail_name': 'new_name', 'email': 'new_email'}

        PATCH: for partial update
            {'mail_name': 'new_name'}
            or
            {'email': 'new_email'}
            or
            {'mail_name': 'new_name', 'email': 'new_email'}

        __URL__:
        /maillists/{instance_pk}

        __Response__:

            {
                "id": int,
                "mail_name": string,
                "email": email_address
            }

        __Example__:

        PUT:

            curl -X PUT -d '{"mail_name": "new_name", "email": "new_email"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/maillists/1/
            # output
            {"id": 1, "mail_name": "new_name", "email": "new_email"}

        PATCH:

            curl -X PATCH -d '{"email": "new_email"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/maillists/1/
            # output
            {"id": 1, "mail_name": "name", "email": "new_email"}
        """
        return super(MaillistViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__:
        /maillists/{instance_pk}

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/maillists/1/
        """
        return super(MaillistViewSet, self).destroy(request, *args, **kwargs)

    serializer_class = MaillistSerializer
    queryset = Maillist.objects.all()
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

        __URL__:
        /contact-roles/

        __Data__:

            {
                'name': string,         # required
            }
        __Response__:

            {
                "name": string,
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"name": "test"}' %(HOST_NAME)s/%(API_PATH)s/contact-roles/
            # output
            {"name": "test"}
        """
        return super(ContactRoleViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__:
        /contact-roles/

        __QUERY Params__:

            name  # optional

        __Response__:

            # paged lists
            {
                "count": 4,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "name": "test_role",
                    },
                    {
                        "name": string,
                    },
                    ...
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X GET %(HOST_NAME)s/%(API_PATH)s/contact-roles/
            # output
            {
                "count": 4,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "name": "qe_leader",
                    },
                    {
                        "name": "qe_group",
                    },
                    ...
                ]
            }

        With query params:

            curl -H "Content-Type: application/json"  -G %(HOST_NAME)s/%(API_PATH)s/contact-roles/ --data-urlencode "name=test"
            # output
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "name": "test",
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

        __URL__:
        /contact-roles/{role_name}

        __Response__:

            {
                "name": string,
            }

        __Example__:

            curl -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/contact-roles/QE_Leader/
            # output
            {"name": "QE_Leader"}
        """
        return super(ContactRoleViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__:
        PUT/PATCH

            {'name': 'new_name'}

        __URL__:
        /contact-roles/{role_name}

        __Response__:

            {
                "name": string,
            }

        __Example__:

        PUT:

            curl -X PUT -d '{"name": "new_name"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/contact-roles/QE_ACK/
            # output
            {"name": "new_name"}

        PATCH:

            curl -X PATCH -d '{"name": "new_name"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/contact-roles/QE_ACK/
            # output
            {"name": "new_name"}
        """
        return super(ContactRoleViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__:
        /contact-roles/{role_name}

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/contact-roles/QE_Group/
        """
        return super(ContactRoleViewSet, self).destroy(request, *args, **kwargs)

    serializer_class = ContactRoleSerializer
    queryset = ContactRole.objects.all()
    filter_class = ContactRoleFilterSet
    lookup_field = 'name'
    overwrite_lookup_field = False


class RoleContactViewSet(viewsets.PDCModelViewSet):
    """
    ##Overview##

    This page shows the usage of the **RoleContact API**, please see the
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

        __URL__:
        /role-contacts/

        __Data__:

            {
                'contact_role':   string,                             # required
                'contact': {                                          # required
                               # create contact with person
                               'username':    string,
                               'email':       email_address
                           }
                           # or
                           {
                               # create contact with maillist
                               'mail_name': string,
                               'email':     email_address
                           }
            }
        __Response__:

            {
                "id": int,
                "contact_role": "qe_group",
                "contact": {
                    "mail_name": string,
                    "email": "email@example.com"
                }
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X POST -d '{"contact_role": "qe_group", "contact": {"username": "test", "email": "test@example.com"}}' %(HOST_NAME)s/%(API_PATH)s/role-contacts/
            # output
            {"id": 1, "contact_role": "qe_group", "contact": {"username": "test", "email": "test@example.com"}}
        """
        return super(RoleContactViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        GET

        __URL__:
        /role-contacts/

        __QUERY Params__:

            contact_role  # optional
            username      # optional
            mail_name     # optional
            email         # optional

        **NOTE:** Support listed query params. The logic is:

        **"OR"** between the values with the same key, e.g. "?email=A&email=B" => "email==A or email==B",

        **"AND"** between all the given keys, e.g. "?contact_role=T&email=C" => "contact_role==T and email==C".

        __Response__:

            # paged lists
            {
                "count": 284,
                "next": "%(HOST_NAME)s/%(API_PATH)s/role-contacts/?page=2",
                "previous": null,
                "results": [
                    {
                        "id": int,
                        "contact_role": "qe_group",
                        "contact": {
                            "mail_name": string,
                            "email": "email@example.com"
                        }
                    },
                    ...
            }

        __Example__:

            curl -H "Content-Type: application/json"  -X GET %(HOST_NAME)s/%(API_PATH)s/role-contacts/
            # output
            {
                "count": 284,
                "next": "%(HOST_NAME)s/%(API_PATH)s/role-contacts/?page=2",
                "previous": null,
                "results": [
                    {
                        "id": int,
                        "contact_role": "qe_group",
                        "contact": {
                            "mail_name": string,
                            "email": "string@example.com"
                        }
                    },
                    ...
                ]
            }

        With query params:

            curl -H "Content-Type: application/json"  -G %(HOST_NAME)s/%(API_PATH)s/role-contacts/ --data-urlencode "username=test"
            # output
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "id": int,
                        "contact_role": "qe_group",
                        "contact": {
                            "username": "test",
                            "email": "test@example.com"
                        }
                    }
                ]
            }
        """
        return super(RoleContactViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        ### RETRIEVE

        __Method__:
        GET

        __URL__:
        /role-contacts/{instance_pk}

        __Response__:

            {
                "id": int,
                "contact_role": "qe_group",
                "contact": {
                    "mail_name": string,
                    "email": "string@example.com"
                }
            }

        __Example__:

            curl -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/role-contacts/1/
            # output
            {"id": 1, "contact_role": "qe_group", "contact": {"username": "test", "email": "test@example.com"}}
        """
        return super(RoleContactViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__:
        PUT: for full fields update

            {
                "contact_role": "new_role",
                "contact": {'username': 'new_name', 'email': 'new_email'}
            }

        PATCH: for partial update

            {
                "contact_role": "new_role",
            }
            or
            {
                "contact": {'username': 'new_name', 'email': 'new_email'}
            }
            or
            {
                "contact_role": "new_role",
                "contact": {'username': 'new_name', 'email': 'new_email'}
            }

        __URL__:
        /role-contacts/{instance_pk}

        __Response__:

            {
                "id": 1,
                "contact_role": "new_role",
                "contact": {
                    "username": "new_name",
                    "email": "new_email"
                }
            }

        __Example__:

        PUT:

            curl -X PUT -d '{"contact_role": "new_role", "contact": {"username": "new_name", "email": "new_email"}}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/role-contacts/1/
            # output
            {"id": 1, "contact_role": "new_role", "contact": {"username": "new_name", "email": "new_email"}}

        PATCH:

            curl -X PATCH -d '{"contact_role": "new_role"}' -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/role-contacts/1/
            # output
            {"id": 1, "contact_role": "new_role", "contact": {"username": "new_name", "email": "new_email"}}
        """
        return super(RoleContactViewSet, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        ### DELETE

        __Method__:
        DELETE

        __URL__:
        /role-contacts/{instance_pk}

        __Response__:

            STATUS: 204 NO CONTENT

        __Example__:

            curl -X DELETE -H "Content-Type: application/json" %(HOST_NAME)s/%(API_PATH)s/role-contacts/1/
        """
        return super(RoleContactViewSet, self).destroy(request, *args, **kwargs)

    serializer_class = RoleContactSerializer
    queryset = RoleContact.objects.all()
    extra_query_params = ('contact_role', 'username', 'mail_name', 'email')

    def get_queryset(self):
        queryset = RoleContact.objects.all()

        filters = self.request.query_params
        person_kwarg = {}
        maillist_kwarg = {}

        if 'contact_role' in filters:
            contact_role_list = ContactRole.objects.filter(name__in=filters.getlist('contact_role'))
            queryset = queryset.filter(contact_role__in=contact_role_list)

        if 'username' in filters:
            person_kwarg["person__username__in"] = filters.getlist('username')
            if 'email' in filters:
                person_kwarg['person__email__in'] = filters.getlist('email')
        if 'mail_name' in filters:
            maillist_kwarg['maillist__mail_name__in'] = filters.getlist('mail_name')
            if 'email' in filters:
                maillist_kwarg['maillist__email__in'] = filters.getlist('email')
        if 'username' not in filters and 'mail_name' not in filters and 'email' in filters:
            person_kwarg['person__email__in'] = filters.getlist('email')
            maillist_kwarg['maillist__email__in'] = filters.getlist('email')

        Q_contacts = Q()
        if person_kwarg:
            persons = Contact.objects.filter(**person_kwarg).values_list('id', flat=True)
            Q_contacts |= Q(contact__in=persons)
        if maillist_kwarg:
            maillists = Contact.objects.filter(**maillist_kwarg).values_list('id', flat=True)
            Q_contacts |= Q(contact__in=maillists)

        return queryset.filter(Q_contacts).distinct()
