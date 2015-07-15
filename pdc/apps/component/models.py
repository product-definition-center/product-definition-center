# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.dispatch import receiver

from mptt import models as mptt_models

from pdc.apps.common.models import Label
from pdc.apps.contact.models import RoleContact
from pdc.apps.common import hacks
from pdc.apps.release.models import Release
from pdc.apps.release import signals


__all__ = [
    'Upstream',
    'GlobalComponent',
    'ReleaseComponent',
    'BugzillaComponent',
    'ReleaseComponentGroup',
    'GroupType'
]


def validate_bc_name(name):
    if "/" in name:
        raise ValidationError("Symbol / is not acceptted as part of bugzilla component's name.")


class Upstream(models.Model):
    homepage        = models.URLField(max_length=200)
    scm_type        = models.CharField(max_length=50, blank=True, null=True)
    scm_url         = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        unique_together = [
            ('homepage', 'scm_type', 'scm_url')
        ]

    def __unicode__(self):
        return u'%s' % self.homepage

    def export(self, fields=None):
        _fields = ['homepage', 'scm_type', 'scm_url'] if fields is None else fields
        result = dict()
        if 'homepage' in _fields:
            result['homepage'] = self.homepage
        if 'scm_type' in _fields:
            result['scm_type'] = self.scm_type
        if 'scm_url' in _fields:
            result['scm_url'] = self.scm_url
        return result


class BugzillaComponent(mptt_models.MPTTModel):
    name                        = models.CharField(max_length=100, validators=[validate_bc_name])
    parent_component = mptt_models.TreeForeignKey('self', null=True, blank=True, related_name='children')

    class Meta:
        unique_together = [
            ("name", "parent_component"),
        ]

    class MPTTMeta:
        parent_attr = 'parent_component'
        order_insertion_by = ['name']

    def __unicode__(self):
        return self.name

    def get_path_name(self):
        bugzilla_subcomponents = []
        for node in self.get_ancestors(include_self=True):
            bugzilla_subcomponents.append(node.name)
        return u"%s" % "/".join(bugzilla_subcomponents)

    def get_subcomponents(self):
        path_name = self.get_path_name()
        result = []
        for descendant in self.get_descendants():
            descendant_path_name = descendant.get_path_name().replace(path_name + '/', "", 1)
            result.append(descendant_path_name)
        return result

    def export(self, fields=None):
        _fields = ['name', 'parent_component', 'subcomponents'] if fields is None else fields
        result = dict()
        if 'name' in _fields:
            result['name'] = self.name
        if 'parent_component' in _fields:
            result['parent_component'] = self.parent_component.name if self.parent_component else None
        if 'subcomponents' in _fields:
            result['subcomponents'] = self.get_subcomponents()
        return result


class GlobalComponent(models.Model):
    """Record generic component"""

    name            = models.CharField(max_length=100, unique=True)
    contacts        = models.ManyToManyField(RoleContact, blank=True)
    dist_git_path   = models.CharField(max_length=200, blank=True, null=True)
    labels          = models.ManyToManyField(Label, blank=True)
    upstream        = models.OneToOneField(Upstream, blank=True, null=True)

    def __unicode__(self):
        return u"%s" % self.name

    @property
    def dist_git_web_url(self):
        dist_git_path = self.dist_git_path or self.name
        if not hasattr(settings, "DIST_GIT_REPO_FORMAT"):
            raise ImproperlyConfigured("'DIST_GIT_REPO_FORMAT' is required in settings.")
        return settings.DIST_GIT_REPO_FORMAT % (dist_git_path)

    def export(self, fields=None):
        _fields = ['name', 'contacts', 'dist_git_path', 'labels', 'upstream'] if fields is None else fields
        result = dict()
        if 'name' in _fields:
            result['name'] = self.name
        if 'contacts' in _fields:
            result['contacts'] = []
            contacts = self.contacts.all()
            if contacts:
                for contact in contacts:
                    result['contacts'].append(contact.export())
        if 'dist_git_path' in _fields:
            result['dist_git_path'] = self.dist_git_path
        if 'labels' in _fields:
            result['labels'] = []
            labels = self.labels.all()
            if labels:
                for label in labels:
                    result['labels'].append(label.export())
        if 'upstream' in _fields:
            result['upstream'] = self.upstream.export() if self.upstream else None
        return result


class ReleaseComponentType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return u"%s" % self.name


class ReleaseComponent(models.Model):
    """Record which release is connecting to which components"""

    release                     = models.ForeignKey(Release)
    global_component            = models.ForeignKey(GlobalComponent)
    bugzilla_component          = models.ForeignKey(BugzillaComponent, blank=True, null=True, on_delete=models.SET_NULL)
    type                        = models.ForeignKey(ReleaseComponentType, blank=True, null=True,
                                                    on_delete=models.SET_NULL, related_name='release_components',)
    name                        = models.CharField(max_length=100)
    dist_git_branch             = models.CharField(max_length=100, blank=True, null=True)
    contacts                    = models.ManyToManyField(RoleContact, blank=True)
    brew_package = models.CharField(max_length=100, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [
            ("release", "global_component", "name"),
        ]

    def __unicode__(self):
        return u"%s %s" % (self.release, self.name)

    def get_contacts(self, include_global=True):
        """
        Get release_component contacts.
        If flag equals True, the contacts will include global_component contacts
        which is not in release_component.
        """
        rc_contacts = [contact.export() for contact in self.contacts.all()]
        if include_global:
            gc_contacts = [contact.export() for contact in self.global_component.contacts.all()]
            contact_role_lists = [contact['contact_role'] for contact in rc_contacts]
            for contact in gc_contacts:
                if contact['contact_role'] in contact_role_lists:
                    continue
                rc_contacts.append(contact)
        return rc_contacts

    @property
    def dist_git_web_url(self):
        if not hasattr(settings, "DIST_GIT_BRANCH_FORMAT"):
            raise ImproperlyConfigured("'DIST_GIT_BRANCH_FORMAT' is required in settings.")
        if self.inherited_dist_git_branch:
            return "".join([self.global_component.dist_git_web_url,
                            settings.DIST_GIT_BRANCH_FORMAT % (self.inherited_dist_git_branch)])
        else:
            return self.global_component.dist_git_web_url

    def _get_inherited_dist_git_branch(self):
        if self.dist_git_branch is None:
            return self.release.dist_git_branch
        else:
            return self.dist_git_branch

    def _set_inherited_dist_git_branch(self, value):
        self.dist_git_branch = value

    inherited_dist_git_branch = property(fget=_get_inherited_dist_git_branch,
                                         fset=_set_inherited_dist_git_branch)

    def export(self, fields=None):
        _fields = ['release', 'global_component', 'name', 'dist_git_branch', 'type',
                   'contacts', 'bugzilla_component', 'brew_package', 'active'] if fields is None else fields
        result = dict()
        for attr in ('name', 'dist_git_branch', 'brew_package', 'active'):
            # We do not use inherited_dist_git_branch here because changeset
            # need to log the real diffs.
            # And if we update dist_git_branch as the same as release,
            # changeset could be show the changes from null to current value.
            if attr in _fields:
                result[attr] = getattr(self, attr)

        if 'type' in _fields:
            result['type'] = self.type.name if self.type else None
        if 'release' in _fields:
            result['release'] = self.release.release_id
        if 'global_component' in _fields:
            result['global_component'] = self.global_component.name
        if 'bugzilla_component' in _fields:
            if self.bugzilla_component:
                result['bugzilla_component'] = "{} (id:{})".format(self.bugzilla_component.name,
                                                                   self.bugzilla_component.id)
            else:
                result['bugzilla_component'] = None
        if 'contacts' in _fields:
            result['contacts'] = []
            contacts = self.contacts.all()
            for contact in contacts:
                result['contacts'].append(contact.export())

        return result


class GroupType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name

    def export(self, fields=None):
        _fields = ['name', 'description'] if fields is None else fields
        result = dict()
        if 'name' in _fields:
            result['name'] = self.name
        if 'description' in _fields:
            result['description'] = self.description
        return result


class ReleaseComponentGroup(models.Model):
    group_type = models.ForeignKey(GroupType, related_name='release_component_groups')
    release = models.ForeignKey(Release, related_name='release_component_groups')
    description = models.CharField(max_length=200)
    components = models.ManyToManyField(ReleaseComponent, related_name='release_component_groups', blank=True)

    def __unicode__(self):
        return u'%s-%s-%s' % (self.release.release_id, self.group_type.name, self.description)

    class Meta:
        unique_together = [
            ('group_type', 'release', 'description')
        ]

    def export(self, fields=None):
        _fields = ['group_type', 'release', 'description', 'components'] if fields is None else fields
        result = dict()
        if 'group_type' in _fields:
            result['group_type'] = self.group_type.name
        if 'release' in _fields:
            result['release'] = self.release.release_id
        if 'description' in _fields:
            result['description'] = self.description
        if 'components' in _fields:
            result['components'] = []
            components = self.components.all()
            if components:
                for component in components:
                    result['components'].append(component.export())
        return result


@receiver(signals.release_clone)
def clone_release_components_and_groups(sender, request, original_release, release, **kwargs):
    data = request.data
    include_inactive = data.pop('include_inactive', None)
    include_inactive = (include_inactive is None or
                        hacks.convert_str_to_bool(include_inactive, name='include_inactive'))
    new_dist_git_branch = data.pop('component_dist_git_branch', None)

    rc_map = dict()
    for rc in ReleaseComponent.objects.filter(release=original_release):
        org_rc_pk = rc.pk
        contacts = rc.contacts.all()
        rc.pk = None
        if not include_inactive and not rc.active:
            continue
        rc.release = release
        if new_dist_git_branch:
            rc.dist_git_branch = new_dist_git_branch
        rc.save()
        rc.contacts.add(*list(contacts))
        request.changeset.add("ReleaseComponent", rc.pk, "null", json.dumps(rc.export()))
        rc_map[org_rc_pk] = rc

    for group in ReleaseComponentGroup.objects.filter(release=original_release):
        group_type = group.group_type
        description = group.description
        org_components = group.components.all()

        group.pk = None
        group.description = description
        group.group_type = group_type
        group.release = release
        group.save()
        for component in org_components:
            new_rc = rc_map.get(component.pk)
            if new_rc:
                group.components.add(new_rc)
        request.changeset.add('ReleaseComponentGroup', group.pk, 'null', json.dumps(group.export()))
