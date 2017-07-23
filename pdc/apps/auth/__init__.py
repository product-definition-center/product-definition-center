# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


"""
PDC Auth
========

This is for supporting kerberos authentication along with anonymous
access. User details can be read from LDAP.

Configuring settings.py
-----------------------

    MIDDLEWARE = (
        ...
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'auth.middleware.KerberosUserMiddleware',
        ...
    )

    AUTHENTICATION_BACKENDS = (
        'auth.backends.KerberosUserBackend',
    )

    # login url for kerberos auth, which should also be configured
    # in apache configration

    LOGIN_URL = '/auth/krb5login'
    LOGIN_REDIRECT_URL = '/'

    # LDAP settings
    LDAP_URI = "ldap://ldap.example.com:389"
    LDAP_USERS_DN = "ou=users,dc=example,dc=com"
    LDAP_GROUPS_DN = "ou=groups,dc=example,dc=com"

    # For debugging purposes, you can mock kerberos login by setting following options:
    DEBUG = True
    DEBUG_USER = "<login>"


Configuring urls.py
-------------------

    urlpatterns = [
        ...
        url(r'^auth/krb5login$', 'auth.views.krb5login', name='auth/krb5login')
        ...
    ]


Configuring Apache
------------------

    ...
    <Location "/auth/krb5login">
        AuthType Kerberos
        AuthName "<project> Kerberos Authentication"
        KrbMethodNegotiate on
        KrbMethodK5Passwd off
        KrbServiceName HTTP
        KrbAuthRealms EXAMPLE.COM
        Krb5Keytab /etc/httpd/conf/http.<hostname>.keytab
        KrbSaveCredentials off
        Require valid-user
    </Location>
    ...

REST API Auth
=============

We use `TokenAuthentication` for API Authentication.
Unauthenticated user will only have the readonly access to APIs.

NOTE: The Browsable API can benefit from session, so it uses `SessionAuthentication`.

Configuring `settings.py`
-----------------------

    INSTALLED_APPS = (
        ...
        'rest_framework.authtoken',
    )
    ...
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
            # SessionAuthentication is only used for the Browsable API.
            'rest_framework.authentication.SessionAuthentication',
        ),
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.DjangoModelPermissions'
        ],
    ...
    }

Configuring Apache
------------------

    ...
    # needed by REST Framework Token Auth
    WSGIPassAuthorization On

    # NOTE: the `url` added in the `urls.py` should be match to or coverd by this `Location`
    # In this example, `Location "/rest_api/v1/auth/token" is sufficient for
    # both `/rest_api/v1/auth/token/obtain` and `/rest_api/v1/auth/token/refresh`.
    <Location "/rest_api/v1/auth/token">
        AuthType Kerberos
        AuthName "<project> API Kerberos Authentication"
        KrbMethodNegotiate on

        # passwd should be disabled
        KrbMethodK5Passwd off

        KrbServiceName HTTP
        KrbAuthRealms EXAMPLE.COM
        Krb5Keytab /etc/httpd/conf/http.<hostname>.keytab
        KrbSaveCredentials off
        Require valid-user
    </Location>
    ...

Using Token
-----------

    # obtain token
    curl --negotiate -u : -H "Accept: application/json"  https://pdc.example.com/rest_api/v1/auth/token/obtain
    # you will get a `Response` like:
    {"token": "00bf04e8187f6e6d54f510515e8bde88e5bb7904"}

    # then you should add one more HTTP HEADER with this token in this format:
    Authorization: Token 00bf04e8187f6e6d54f510515e8bde88e5bb790
    # for curl, it should be:
    curl -H 'Authorization: Token 00bf04e8187f6e6d54f510515e8bde88e5bb790' https://pdc.example.com/rest_api/v1/

"""

default_app_config = 'pdc.apps.auth.apps.AuthConfig'
