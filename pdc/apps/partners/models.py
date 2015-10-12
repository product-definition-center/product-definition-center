# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db import models


class PartnerType(models.Model):
    name = models.CharField(unique=True, max_length=100)

    def __unicode__(self):
        return unicode(self.name)


class Partner(models.Model):
    short = models.CharField(unique=True, max_length=100, blank=False)
    name = models.CharField(max_length=250, blank=False)
    type = models.ForeignKey(PartnerType)
    binary = models.BooleanField(default=True)
    source = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)
    ftp_dir = models.CharField(max_length=500)
    rsync_dir = models.CharField(max_length=500)

    def __unicode__(self):
        return u'{0.short} ({0.name})'.format(self)

    def export(self):
        result = {'type': self.type.name}
        for attr in ['short', 'name', 'binary', 'source', 'enabled', 'ftp_dir', 'rsync_dir']:
            result[attr] = getattr(self, attr)
        return result


class PartnerMapping(models.Model):
    partner = models.ForeignKey(Partner)
    variant_arch = models.ForeignKey('release.VariantArch')

    class Meta:
        unique_together = (('partner', 'variant_arch'), )

    def __unicode__(self):
        return u'{} {} {}'.format(self.partner, self.variant_arch.variant.release,
                                  self.variant_arch)

    def export(self):
        return {
            'partner': unicode(self.partner),
            'release': unicode(self.variant_arch.variant.release),
            'variant_arch': unicode(self.variant_arch)
        }
