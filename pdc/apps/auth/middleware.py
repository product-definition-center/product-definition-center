# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


from django.contrib import auth
from django.conf import settings
from django.contrib.auth import load_backend
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.core.exceptions import ImproperlyConfigured


class RemoteUserMiddleware(RemoteUserMiddleware):
    def process_request(self, request):
        # Overwrite process_request from auth.middleware because it force
        # user logout when REMOTE_USER header is not present which can
        # cause problem while deploying with Kerberos authentication when
        # we need to enable both anonymous access and kerberos login.

        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class.")

        if settings.DEBUG and getattr(settings, "DEBUG_USER", None):
            request.META[self.header] = settings.DEBUG_USER

        try:
            username = request.META[self.header]
        except KeyError:
            # When the page which requires kerberos login was redirected from
            # kerberos login entrance, 'REMOTE_USER' header is lost in request
            # meta, thus the RemoteUserMiddleware will make it falling into
            # redirect loop.
            return

        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
            if request.user.get_username() == self.clean_username(username, request):
                return
        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(remote_user=username, request=request)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            request.session['auth_backend'] = user.backend
            backend = load_backend(user.backend)
            if getattr(backend, 'save_login', True):
                auth.login(request, user)
