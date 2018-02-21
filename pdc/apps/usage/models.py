#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db import models
from django.conf import settings


class ResourceUsage(models.Model):
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    resource    = models.CharField(max_length=300)
    method      = models.CharField(max_length=10)
    time        = models.DateTimeField()

    class Meta:
        unique_together = ('resource', 'method')

    def __unicode__(self):
        return '%s %s' % (self.method, self.resource)
