#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
from django.db import models
from pdc.apps.package.models import RPM


class Module(models.Model):
    variant_id  = models.CharField(max_length=100, blank=False)
    uid         = models.CharField(max_length=610, blank=False, unique=True)
    name        = models.CharField(max_length=300, blank=False)
    stream      = models.CharField(max_length=100, blank=False)
    version     = models.CharField(max_length=100, blank=False)
    context     = models.CharField(max_length=100, blank=False)
    # No new instances should have a `type` value other than `module`. This is here just for
    # backwards compatibility with the `unreleasedvariants` API.
    type        = models.CharField(max_length=100, blank=False, default='module')
    active      = models.BooleanField(default=False)
    koji_tag    = models.CharField(max_length=300, blank=False)
    modulemd    = models.TextField(blank=False)
    rpms        = models.ManyToManyField(RPM)

    class Meta:
        ordering = ('name', 'stream', 'version', 'context')
        unique_together = (
            ('name', 'stream', 'version', 'context'),
        )

    def __unicode__(self):
        return u'%s' % (self.uid, )

    def export(self):
        return {
            'variant_id': self.variant_id,
            'uid': self.uid,
            'name': self.name,
            'stream': self.stream,
            'version': self.version,
            'context': self.context,
            'type': self.type,
            'active': self.active,
            'koji_tag': self.koji_tag,
            'modulemd': self.modulemd,
            'rpms': [obj.export() for obj in self.rpms.all()],
            'runtime_deps': [v.dependency for v in self.runtime_deps.all()],
            'build_deps': [v.dependency for v in self.build_deps.all()],
        }


class ModuleDependency(models.Model):
    dependency = models.CharField(max_length=300)
    stream = models.CharField(max_length=300)

    class Meta:
        abstract = True


class RuntimeDependency(ModuleDependency):
    variant = models.ForeignKey('Module', related_name='runtime_deps')


class BuildDependency(ModuleDependency):
    variant = models.ForeignKey('Module', related_name='build_deps')
