# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.shortcuts import render, redirect
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.contrib.auth.models import Group, Permission
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import mixins, viewsets

from . import backends
from . import filters
from . import serializers
from pdc.apps.common.viewsets import StrictQueryParamMixin, ChangeSetUpdateModelMixin
from pdc.apps.utils.utils import group_obj_export


def krb5login(request):
    # if REDIRECT_FIELD_NAME is present in request.GET and has blank
    # value, that can cause redirect loop while redirecting to it
    redirect_to = request.GET.get(REDIRECT_FIELD_NAME, '/').strip() or '/'

    if request.user.is_authenticated() and request.user.is_active:
        return HttpResponseRedirect(redirect_to)

    try:
        request.session.flush()
    except Exception:
        pass

    if request.user.is_anonymous():
        reason = "Failed to authenticate with Kerberos. Make sure your browser is correctly configured."
    elif not request.user.is_active:
        reason = "Account is not active."

    context = {'reason': reason}
    return render(request, 'no_krb5.html', context)


def user_profile(request):
    context = {'has_ldap': hasattr(settings, "LDAP_URI")}
    return render(request, 'user_profile.html', context)


def refresh_ldap_groups(request):
    user = request.user
    backends.update_user_from_ldap(user)
    if request.is_ajax():
        return HttpResponse(json.dumps({
            'username': user.username,
            'fullname': user.first_name + ' ' + user.last_name,
            'e-mail': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'groups': [g.name for g in user.groups.all()],
            'permissions': list(user.get_all_permissions()),
        }), content_type="application/json")
    return redirect("user/profile")


class TokenViewSet(StrictQueryParamMixin, viewsets.ViewSet):
    """
    ## REST API Auth ##

    We use `TokenAuthentication` for API Authentication.

    Unauthenticated user will not be able to access to APIs.

    **WARNING:** Please do not share your token with anyone else.

    **NOTE:** It's highly recommended to make sure your API is only available over `https` when using `TokenAuthentication`.

    We use DjangoModelPermissions for RESTful API permissions.

    Authorization will only be granted if the user is authenticated
    and has the relevant model permissions assigned.

    * __POST__ requests require the user to have the `add` permission on the model.
    * __PUT__ and __PATCH__ requests require the user to have the `change` permission on the model.
    * __DELETE__ requests require the user to have the `delete` permission on the model.

    ### Using Token

    * obtain token

            curl --negotiate -u : -H "Content-Type: application/json"  $URL:token-obtain$

        you will get a `Response` like:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}

    * then you should add one HTTP HEADER with this token in this format with every request need authentication:

            Authorization: Token 00bf04e8187f6e6d54f510515e8bde88e5bb790

        for curl, it should be:

            curl -H 'Authorization: Token 00bf04e8187f6e6d54f510515e8bde88e5bb790' %(HOST_NAME)s/%(API_PATH)s/

    * in case you want refresh your token, you can do it with:

            curl --negotiate -u : -H "Content-Type: application/json"  $URL:token-refresh$

        you will get a `Response` with refreshed token:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}

    """

    permission_classes = [IsAuthenticated]

    # Dummy list view for showing ViewSet docstring.
    def list(self, request):
        return Response()

    @list_route(methods=['get', 'post'])
    def obtain(self, request):
        """
        ### Obtain Token

        __URL__: $LINK:token-obtain$

        __EXAMPLE__:

        Run:

            curl --negotiate -u : -H "Content-Type: application/json"  $URL:token-obtain$

        you will get a `Response` like:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}
        """

        if request.user.is_authenticated():
            if request.user.is_active:
                token, created = Token.objects.get_or_create(user=request.user)
                return Response({'token': token.key})
            else:
                reason = {"Obtain Token Error": "You're not an active user."}
                return Response(reason, status=status.HTTP_401_UNAUTHORIZED)
        else:
            reason = {"Obtain Token Error": "Failed to authenticate."}
            return Response(reason, status=status.HTTP_401_UNAUTHORIZED)

    @list_route(methods=['get', 'put'])
    def refresh(self, request):
        """
        ### Refresh Token

        __URL__: $LINK:token-refresh$

        __EXAMPLE__:

        Run:

            curl --negotiate -u : -H "Content-Type: application/json"  $URL:token-refresh$
            # or
            curl --negotiate -u : -X PUT -H "Content-Type: application/json"  $URL:token-refresh$

        you will get a `Response` with refreshed token:

            {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}
        """
        if request.user.is_authenticated():
            if request.user.is_active:
                try:
                    token = Token.objects.get(user=request.user)
                    token.delete()
                except Token.DoesNotExist:
                    reason = {"Refresh Token Error": "You have not got a token yet, please try obtain first."}
                    return Response(reason, status=status.HTTP_400_BAD_REQUEST)
                token = Token.objects.create(user=request.user)
                return Response({'token': token.key})
            else:
                reason = {"Refresh Token Error": "You're not an active user."}
                return Response(reason, status=401)
        else:
            reason = {"Refresh Token Error": "Authenticate Failed."}
            return Response(reason, status=401)


class PermissionViewSet(StrictQueryParamMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    ##Overview##

    This page shows the usage of the **Permission API**, please see the
    following for more details.

    """

    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        `GET`

        __QUERY Params__:

        %(FILTERS)s

        __URL__: $LINK:permission-list$

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            curl -H "Content-Type: application/json"  -X GET $URL:permission-list$
            # output
            {
                "count": 150,
                "next": "$URL:permission-list$?page=2",
                "previous": null,
                "results": [
                    {
                        "codename": "add_logentry",
                        "app_label": "admin",
                        "model": "logentry"
                    },
                    ...
                ]
            }

        With query params:

            curl -H "Content-Type: application/json"  -G $URL:permission-list$ --data-urlencode "codename=add_logentry"
            # output
            {
                "count": 1,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "codename": "add_logentry",
                        "app_label": "admin",
                        "model": "logentry"
                    }
                ]
            }

        """
        return super(PermissionViewSet, self).list(request, *args, **kwargs)

    queryset = Permission.objects.all()
    serializer_class = serializers.PermissionSerializer
    filter_class = filters.PermissionFilter


class GroupViewSet(ChangeSetUpdateModelMixin,
                   StrictQueryParamMixin,
                   mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   viewsets.GenericViewSet):
    """
    ##Overview##

    This page shows the usage of the **Group API**, please see the
    following for more details.
    """
    def list(self, request, *args, **kwargs):
        """
        ### LIST

        __Method__:
        `GET`

        __URL__: $LINK:group-list$

        __QUERY Params__:

        %(FILTERS)s

        __Response__: a paged list of following objects

        %(SERIALIZER)s

        __Example__:

            {
                "count": 2,
                "next": null,
                "previous": null,
                "results": [
                    {
                        "url": "$URL:group-detail:1$",
                        "name": "group_add_group",
                        "permissions": [
                            {
                                "codename": "add_group",
                                "app_label": "auth",
                                "model": "group"
                            }
                        ]
                    },
                    {
                        "url": "$URL:group-detail:2$",
                        "name": "group_change_change",
                        "permissions": [
                            {
                                "codename": "change_change",
                                "app_label": "changeset",
                                "model": "change"
                            }
                        ]
                    }
                ]
            }

        """
        return super(GroupViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        ### RETRIEVE

        __Method__:
        `GET`

        __URL__: $LINK:group-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

            # curl command
            curl -H "Content-Type: application/json" $URL:group-detail:1$
            # output
            {
              "url": "$URL:group-detail:1$,
              "name": "group_add_group",
              "permissions": [
                  {
                      "codename": "add_group",
                      "app_label": "auth",
                      "model": "group"
                  }
              ]
            }
        """
        return super(GroupViewSet, self).retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        ### UPDATE

        __Method__:

        `PUT`: to update name and permissions

        `PATCH`: to update name or permissions

        __URL__: $LINK:group-detail:instance_pk$

        __Response__:

        %(SERIALIZER)s

        __Example__:

        PUT:

            # cat put_data.json
            {
                "name": "new_group",
                "permissions": [
                    {
                        "codename": "change_change",
                        "app_label": "changeset",
                        "model": "change"
                    },
                    {
                        "codename": "add_group",
                        "app_label": "auth",
                        "model": "group"
                    }
                ]
            }
            # curl command
            curl -H "Content-Type: application/json" \\
                 -X PUT \\
                 --data @put_data.json  \\
                $URL:group-detail:1$
            # output
            {
              "url": "$URL:group-detail:1$",
              "name": "new_group",
              "permissions": [
                  {
                      "codename": "change_change",
                      "app_label": "changeset",
                      "model": "change"
                  },
                  {
                      "codename": "add_group",
                      "app_label": "auth",
                      "model": "group"
                  }
              ]
            }

        PATCH:

            # cat patch_data.json
            {
                "permissions": [
                    {
                        "codename": "change_change",
                        "app_label": "changeset",
                        "model": "change"
                    },
                    {
                        "codename": "add_group",
                        "app_label": "auth",
                        "model": "group"
                    }
                ]
            }
            # curl command
            curl -H "Content-Type: application/json" \\
                 -X PATCH \\
                 --data @patch_data.json  \\
                $URL:group-detail:1$
            # output
            {
              "url": "$URL:group-detail:1$",
              "name": "group_add_group",
              "permissions": [
                  {
                      "codename": "change_change",
                      "app_label": "changeset",
                      "model": "change"
                  },
                  {
                      "codename": "add_group",
                      "app_label": "auth",
                      "model": "group"
                  }
              ]
            }

        """
        return super(GroupViewSet, self).update(request, *args, **kwargs)

    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    filter_class = filters.GroupFilter
    Group.export = group_obj_export


class CurrentUserViewSet(mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    """
    This end-point provides programmatic access to information about current
    user.
    """
    queryset = get_user_model().objects.none()

    def list(self, request):
        """
        Get information about current user.

        __Method__: `GET`

        __URL__: $LINK:currentuser-list$

        __Response__:

            {
                "username": string,
                "fullname": string,
                "e-mail": string,
                "is_superuser": bool,
                "is_staff": bool,
                "groups": [string],
                "permissions": [string]
            }
        """
        user = request.user
        if not user.is_authenticated():
            return Response(status=status.HTTP_401_UNAUTHORIZED,
                            data={'detail': 'Access denied to unauthorized users.'})
        return Response(data={
            'username': user.username,
            'fullname': user.get_full_name(),
            'e-mail': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'groups': [g.name for g in user.groups.all()],
            'permissions': list(user.get_all_permissions()),
        })
