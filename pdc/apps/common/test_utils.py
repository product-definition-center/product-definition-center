#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import authenticate
from exceptions import AssertionError

from pdc.apps.changeset import models


class ChangesetMock(object):
    def __init__(self):
        self.num_changes = 0
        self.changes = []

    def add(self, target_class, target_id, old, new):
        self.changes.append((target_class, target_id, old, new))
        self.num_changes += 1


def create_user(username, groups=None, perms=None, is_super=False):
    email = "%s@example.com" % username
    password = username
    try:
        get_user_model().objects.filter(username=username).delete()
    except Exception:
        pass
    if is_super:
        user = get_user_model().objects.create_superuser(username, email, password)
    else:
        user = get_user_model().objects.create_user(username, email, password)
    groups = groups or []
    for group_name in groups:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group.id)
    perms = perms or []
    for perm_name in perms:
        app_label, codename = perm_name.split(".")
        content_type, _ = ContentType.objects.get_or_create(app_label=app_label, model="")
        perm, _ = Permission.objects.get_or_create(codename=codename, name=perm_name, content_type=content_type)
        user.user_permissions.add(perm)
    user = authenticate(username=username, password=password)
    return user


class TestCaseWithChangeSetMixin(object):
    def assertNumChanges(self, num_changes=[]):
        """
        Check that there is expected number of changes with expected number of
        changes in each. Argument should be a list containing numbers of
        changes in respective changesets.
        """
        changesets = models.Changeset.objects.all()
        if len(changesets) != len(num_changes):
            raise AssertionError('Expected %d changesets, found %d' % (len(num_changes), len(changesets)))
        for i, (changeset, num) in enumerate(zip(changesets, num_changes)):
            if num != changeset.change_set.count():
                raise AssertionError('Wrong number of changes in change set %d, expected %d, got %d'
                                     % (i, num, changeset.change_set.count()))
        return True
