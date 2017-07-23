#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.dispatch import receiver
from django.db import models

from pdc.apps.release.models import Release
from pdc.apps.release import signals as release_signals
from pdc.apps.component import signals as releasecomponent_signals
from pdc.apps.component.models import ReleaseComponent


class ReleaseBugzillaMapping(models.Model):
    release          = models.OneToOneField(Release, on_delete=models.CASCADE)
    bugzilla_product = models.CharField(max_length=200)

    def __unicode__(self):
        return '%s (%s)' % (self.bugzilla_product, self.release.release_id)

    def export(self):
        return {'release_id': self.release.release_id,
                'bugzilla_product': self.bugzilla_product}


Release.bugzilla_product = property(
    lambda self: self.releasebugzillamapping.bugzilla_product
    if hasattr(self, 'releasebugzillamapping') else None
)


@receiver(release_signals.release_clone)
def log_cloned_bugzilla_mapping(sender, request, release, **kwargs):
    if release.bugzilla_product:
        request.changeset.add('ReleaseBugzillaMapping',
                              release.releasebugzillamapping.pk,
                              'null',
                              json.dumps(release.releasebugzillamapping.export()))


@receiver(release_signals.release_post_update)
def log_change_in_bugzilla_mapping(sender, request, release, **kwargs):
    """
    This handler is executed after a new release is saved or an existing
    release is updated. It looks if there is saved old value for bugzilla
    mapping and creates appropriate changelog entries.
    """
    old_data = getattr(request, '_old_bindings_data', {})
    if release.bugzilla_product:
        old_val = 'null'
        if 'bugzilla_mapping' in old_data:
            old_val = old_data['bugzilla_mapping'][1]
        request.changeset.add('ReleaseBugzillaMapping',
                              release.releasebugzillamapping.pk,
                              old_val,
                              json.dumps(release.releasebugzillamapping.export()))
    elif 'bugzilla_mapping' in old_data:
        old_id, old_val = old_data['bugzilla_mapping']
        request.changeset.add('ReleaseBugzillaMapping', old_id, old_val, 'null')


@receiver(release_signals.release_pre_update)
def store_original_bugzilla_mapping(sender, request, release, **kwargs):
    """
    This handler is executed before an existing release is updated. It stores
    the old values for bugzilla mapping in the request.
    """
    if not hasattr(request, '_old_bindings_data'):
        request._old_bindings_data = {}
    if release.bugzilla_product:
        request._old_bindings_data['bugzilla_mapping'] = (
            release.releasebugzillamapping.pk,
            json.dumps(release.releasebugzillamapping.export())
        )


class ReleaseDistGitMapping(models.Model):
    release          = models.OneToOneField(Release, related_name='releasedistgitmapping', on_delete=models.CASCADE)
    dist_git_branch  = models.CharField(max_length=200)

    def __unicode__(self):
        return '%s (%s)' % (self.dist_git_branch, self.release.release_id)

    def export(self):
        return {'release_id': self.release.release_id,
                'dist_git_branch': self.dist_git_branch}


Release.dist_git_branch = property(
    lambda self: self.releasedistgitmapping.dist_git_branch if hasattr(self, 'releasedistgitmapping') else None
)


@receiver(release_signals.release_pre_update)
def store_original_dist_git_mapping(sender, request, release, **kwargs):
    """
    This handler is executed before an existing release is updated. It stores
    the old values for dist_git mapping in the request.
    """
    if not hasattr(request, '_old_bindings_data'):
        request._old_bindings_data = {}
    if release.dist_git_branch:
        request._old_bindings_data['dist_git_mapping'] = (
            release.releasedistgitmapping.pk,
            json.dumps(release.releasedistgitmapping.export())
        )


@receiver(release_signals.release_post_update)
def log_change_in_dist_git_mapping(sender, request, release, **kwargs):
    """
    This handler is executed after a new release is saved or an existing
    release is updated. It looks if there is saved old value for dist_git
    mapping and creates appropriate changelog entries.
    """
    old_data = getattr(request, '_old_bindings_data', {})
    if release.dist_git_branch:
        old_val = 'null'
        if 'dist_git_mapping' in old_data:
            old_val = old_data['dist_git_mapping'][1]
        request.changeset.add('ReleaseDistGitMapping',
                              release.releasedistgitmapping.pk,
                              old_val,
                              json.dumps(release.releasedistgitmapping.export()))
    elif 'dist_git_mapping' in old_data:
        old_id, old_val = old_data['dist_git_mapping']
        request.changeset.add('ReleaseDistGitMapping', old_id, old_val, 'null')


@receiver(release_signals.release_clone)
def log_cloned_dist_git_mapping(sender, request, release, **kwargs):
    if hasattr(release, 'releasedistgitmapping'):
        request.changeset.add('ReleaseDistGitMapping',
                              release.releasedistgitmapping.pk,
                              'null',
                              json.dumps(release.releasedistgitmapping.export()))


class ReleaseComponentSRPMNameMapping(models.Model):
    release_component = models.OneToOneField(ReleaseComponent,
                                             related_name='srpmnamemapping',
                                             on_delete=models.CASCADE)
    srpm_name         = models.CharField(max_length=200, db_index=True)

    def __unicode__(self):
        return u"%s - %s" % (self.release_component.name, self.srpm_name)

    @classmethod
    def get_component_names_by_srpm_name(cls, srpm_name):
        if cls.objects.filter(srpm_name=srpm_name):
            return cls.objects.filter(srpm_name=srpm_name).values_list('release_component__name')
        else:
            return [srpm_name]

    def export(self):
        return {'release_component_id': self.release_component.pk,
                'release_component_name': self.release_component.name,
                'srpm_name': self.srpm_name}


ReleaseComponent.srpm_name = property(
    lambda self: self.srpmnamemapping.srpm_name
    if hasattr(self, 'srpmnamemapping') else None
)


@receiver(releasecomponent_signals.releasecomponent_pre_update)
def store_original_srpm_name_mapping(sender, request, release_component, **kwargs):
    """
    This handler is executed before an release_component is updated. It stores
    the old values for srpm_name mapping in the request.
    """
    if not hasattr(request, '_old_bindings_data'):
        request._old_bindings_data = {}
    if release_component.srpm_name:
        request._old_bindings_data['srpm_name_mapping'] = (
            release_component.srpmnamemapping.pk,
            json.dumps(release_component.srpmnamemapping.export())
        )


@receiver(releasecomponent_signals.releasecomponent_post_update)
def log_change_in_srpm_name_mapping(sender, request, release_component, **kwargs):
    """
    This handler is executed after a release_component is updated.
    It looks if there is saved old value for srpm_name
    mapping and creates appropriate changelog entries.
    """
    old_data = getattr(request, '_old_bindings_data', {})
    if release_component.srpm_name:
        old_val = 'null'
        if 'srpm_name_mapping' in old_data:
            old_val = old_data['srpm_name_mapping'][1]
        request.changeset.add('ReleaseComponentSRPMNameMapping',
                              release_component.srpmnamemapping.pk,
                              old_val,
                              json.dumps(release_component.srpmnamemapping.export()))
    elif 'srpm_name_mapping' in old_data:
        old_id, old_val = old_data['srpm_name_mapping']
        request.changeset.add('ReleaseComponentSRPMNameMapping', old_id, old_val, 'null')
