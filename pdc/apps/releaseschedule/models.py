# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from datetime import datetime

from django.db import models

from pdc.apps.release.models import Release
from pdc.apps.componentbranch.models import SLA


class ReleaseSchedule(models.Model):
    """Record the schedules that releases follow"""

    release     = models.ForeignKey(Release, on_delete=models.CASCADE)
    sla         = models.ForeignKey(SLA, on_delete=models.CASCADE)
    date        = models.DateField(db_index=True)

    class Meta:
        unique_together = [
            ("release", "sla"),
        ]
        ordering = ["date"]
        get_latest_by = "date"

    def __unicode__(self):
        return u"%s %s" % (self.release, self.sla)

    @property
    def active(self):
        return datetime.utcnow().date() <= self.date

    def export(self, fields=None):
        fields = fields or [
            "release", "sla", "date",
        ]
        result = dict()
        if 'release' in fields:
            result['release'] = self.release.release_id
        if 'sla' in fields:
            result['sla'] = self.sla.name
        if 'date' in fields:
            result['date'] = self.date.isoformat()
        for attr in ['active']:
            if attr in fields:
                result[attr] = getattr(self, attr)
        return result
