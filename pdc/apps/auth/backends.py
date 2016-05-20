# -*- coding: utf-8 -*-
#
# Copyright (c) 2015-2016 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import ldap

from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import Group


def get_ldap_groups(l, login):
    groups = l.search_s(settings.LDAP_GROUPS_DN,
                        ldap.SCOPE_SUBTREE,
                        "(memberUid=%s)" % login,
                        ['cn'])
    result = set()
    for i in groups:
        result.update(i[1]["cn"])
    result.discard(login)   # remove user group
    return sorted(result)


def get_ldap_user(l, login):
    user = l.search_s(settings.LDAP_USERS_DN, ldap.SCOPE_SUBTREE, "(uid=%s)" % login)
    if not user:
        return None
    user = user[0]
    return {
        "login": user[1]["uid"][0],
        "full_name": user[1]["givenName"][0] + ' ' + user[1]["sn"][0],
        "email": user[1]["mail"][0],
    }


def update_user_from_ldap(user, conn=None):
    """
    Sync given user with LDAP. Use `conn` as connection if supplied, otherwise
    create a new connection and unbind it when syncing is done. Passed
    connection is not closed.
    """
    if "/" in user.username:
        # host principal -> no record in ldap
        return

    if not getattr(settings, "LDAP_URI", None):
        return

    try:
        l = conn or ldap.initialize(settings.LDAP_URI)
        user_data = get_ldap_user(l, user.username)
        groups = get_ldap_groups(l, user.username)
    finally:
        if not conn:
            l.unbind()

    if user_data:
        user.full_name = user_data["full_name"]
        user.email = user_data["email"]

    group_ids = set()
    for group_name in groups:
        group, _ = Group.objects.get_or_create(name=group_name)
        group_ids.add(group.id)
    user.groups = group_ids

    user.save()


def update_user_from_auth_mellon(user, request):
    user.full_name = request.META['MELLON_fullname']
    user.email = request.META['MELLON_email']

    group_ids = set()
    for var in request.META:
        if var.startswith('MELLON_groups_'):
            group_name = request.META[var]
            group, _ = Group.objects.get_or_create(name=group_name)
            group_ids.add(group.id)
    user.groups = group_ids

    user.save()


def update_user_from_auth_oidc(user, request):
    user.full_name = request.META['OIDC_CLAIM_name']
    user.email = request.META['OIDC_CLAIM_email']

    group_ids = set()
    for group_name in request.META['OIDC_CLAIM_groups'].split(','):
        group, _ = Group.objects.get_or_create(name=group_name)
        group_ids.add(group.id)
    user.groups = group_ids

    user.save()


class KerberosUserBackend(RemoteUserBackend):
    # TODO:
    # * handle inactive users (mark inactive, remove groups)
    # * sync daily all users (cron-job?)

    def authenticate(self, remote_user, **kwargs):
        return super(KerberosUserBackend, self).authenticate(remote_user)

    def clean_username(self, username):
        # remove @REALM from username
        return username.split('@')[0]

    def configure_user(self, user):
        """Fetch user data from LDAP and update the user."""
        user = super(KerberosUserBackend, self).configure_user(user)
        update_user_from_ldap(user)
        user.set_unusable_password()
        user.save()
        return user


class AuthMellonUserBackend(RemoteUserBackend):
    save_login = False
    logout_url = '/saml2/logout?ReturnTo='

    def authenticate(self, remote_user, request, **kwargs):
        user = super(AuthMellonUserBackend, self).authenticate(remote_user)
        if user:
            update_user_from_auth_mellon(user, request)
        return user


class AuthOIDCUserBackend(RemoteUserBackend):
    save_login = False
    logout_url = '/oidc_redirect?logout='

    def authenticate(self, remote_user, request, **kwargs):
        user = super(AuthOIDCUserBackend, self).authenticate(remote_user)
        if user:
            update_user_from_auth_oidc(user, request)
        return user
