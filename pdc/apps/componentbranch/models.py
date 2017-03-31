#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from django.db import models

from pdc.apps.component.models import GlobalComponent, ReleaseComponentType


class ComponentBranch(models.Model):
    global_component = models.ForeignKey(GlobalComponent)
    name = models.CharField(max_length=300)
    type = models.ForeignKey(ReleaseComponentType)
    # TODO: Should we include a the dist-git URL?
    # dist_git_url = models.CharField(max_length=500, blank=True)
    critical_path = models.BooleanField(default=False)

    class Meta:
        unique_together = [
            ('global_component', 'name', 'type'),
        ]

    def __unicode__(self):
        return u'{0}: {1} ({2})'.format(
            self.global_component.name, self.name, self.type)

    def export(self):
        return {
            'global_component_name': self.global_component.name,
            'name': self.name,
            'type_name': self.type.name,
            'slas': [{'name': sla_to_branch.sla.name,
                      'eol': sla_to_branch.eol.strftime('%Y-%m-%d')}
                     for sla_to_branch in self.slas.all()],
            'critical_path': self.critical_path
        }


class SLA(models.Model):
    name = models.CharField(max_length=300, unique=True)
    description = models.TextField(blank=True)

    def __unicode__(self):
        return u'{0}'.format(self.name)

    def export(self):
        return {
            'name': self.name,
            'description': self.description,
        }


class SLAToComponentBranch(models.Model):
    sla = models.ForeignKey(SLA, on_delete=models.CASCADE)
    branch = models.ForeignKey(ComponentBranch, related_name='slas',
                               on_delete=models.CASCADE)
    eol = models.DateField()

    class Meta:
        unique_together = [
            ('sla', 'branch'),
        ]

    def __unicode__(self):
        return u'{0} support for {1} {2} ({3})'.format(
            self.sla.name, self.branch.global_component.name, self.branch.name,
            self.branch.type.name)

    def export(self):
        return {
            'sla': self.sla.name,
            'branch': self.branch.name,
            'eol': self.eol.strftime('%Y-%m-%d')
        }
