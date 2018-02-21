# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


from django.db import models
from django.core.exceptions import ValidationError

from pdc.apps.common.models import get_cached_id


class Service(models.Model):
    # rhn, cdn, ftp
    name          = models.CharField(max_length=50, unique=True)
    description   = models.CharField(max_length=200)

    def __unicode__(self):
        return u"%s" % self.name

    CACHE = {}

    @classmethod
    def get_cached_id(cls, value):
        """cached `name` to `id`"""
        return get_cached_id(cls, "name", value)

    def export(self):
        return {
            'name': self.name,
            'description': self.description
        }


class ContentFormat(models.Model):
    # rpm, kickstart, iso
    name          = models.CharField(max_length=50, unique=True)
    pdc_endpoint = models.CharField(max_length=200, null=True)
    description   = models.CharField(max_length=200)

    def __unicode__(self):
        return u"%s" % self.name


class ContentCategory(models.Model):
    # binary, debug, source
    name          = models.CharField(max_length=50, unique=True)
    description   = models.CharField(max_length=200)

    def __unicode__(self):
        return u"%s" % self.name

    CACHE = {}

    @classmethod
    def get_cached_id(cls, value):
        """cached `name` to `id`"""
        return get_cached_id(cls, "name", value)


class RepoFamily(models.Model):
    # dist, beta, htb
    name          = models.CharField(max_length=50, unique=True)
    description   = models.CharField(max_length=200)

    def __unicode__(self):
        return u"%s" % self.name


class RepoManager(models.Manager):
    def get_queryset(self):
        return super(RepoManager, self).get_queryset().select_related("variant_arch", "variant_arch__variant",
                                                                      "variant_arch__variant__release", "service",
                                                                      "repo_family", "content_format",
                                                                      "content_category")


class Repo(models.Model):
    variant_arch        = models.ForeignKey("release.VariantArch",
                                            related_name="repos",
                                            on_delete=models.PROTECT)
    service             = models.ForeignKey(Service, on_delete=models.CASCADE)
    repo_family         = models.ForeignKey(RepoFamily, on_delete=models.CASCADE)
    content_format      = models.ForeignKey(ContentFormat, on_delete=models.CASCADE)
    content_category    = models.ForeignKey(ContentCategory, on_delete=models.CASCADE)
    shadow              = models.BooleanField(default=False)
    name                = models.CharField(max_length=2000, db_index=True)
    # Store engineering product ID which is used to identify products shipped via CDN
    # Next step would be product certificate attached to each compose variant, refer to PDC-504
    product_id          = models.PositiveIntegerField(blank=True, null=True)

    objects = RepoManager()

    class Meta:
        unique_together = ("variant_arch", "service", "repo_family", "content_format", "content_category", "name", "shadow")
        ordering = ["name"]

    def __unicode__(self):
        return u"%s" % self.name

    def export(self):
        return {
            "release_id": self.variant_arch.variant.release.release_id,
            "variant_uid": self.variant_arch.variant.variant_uid,
            "arch": self.variant_arch.arch.name,
            "service": self.service.name,
            "repo_family": self.repo_family.name,
            "content_format": self.content_format.name,
            "content_category": self.content_category.name,
            "name": self.name,
            "shadow": self.shadow,
            "product_id": self.product_id
        }

    @property
    def tree(self):
        """Return a string representation of a tree the repo belongs to."""
        return '%s.%s' % (self.variant_arch.variant.variant_uid,
                          self.variant_arch.arch.name)


class PushTarget(models.Model):
    name = models.CharField(max_length=100, blank=False, db_index=True, unique=True)
    description = models.CharField(max_length=300, blank=True)
    host = models.URLField(max_length=255, blank=True)
    service = models.ForeignKey(Service)

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return u"%s" % self.name

    def export(self):
        return {
            "name": self.name,
            "description": self.description,
            "host": self.host,
            "service": self.service.name,
        }


class MultiDestination(models.Model):
    global_component = models.ForeignKey('component.GlobalComponent')
    origin_repo = models.ForeignKey(Repo, related_name='origin_repo')
    destination_repo = models.ForeignKey(Repo, related_name='destination_repo')
    subscribers = models.ManyToManyField('contact.Person', blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('global_component', 'origin_repo', 'destination_repo')
        ordering = ['global_component']

    def __unicode__(self):
        return u"%s, %s -> %s" % (
            self.global_component.name, self.origin_repo.name, self.destination_repo.name)

    def export(self):
        return {
            "global_component": self.global_component.name,
            "origin_repo_id": self.origin_repo.id,
            "destination_repo_id": self.destination_repo.id,
            "subscribers": [subscriber.username for subscriber in self.subscribers.all()],
            "active": self.active,
        }

    def clean(self):
        if self.origin_repo == self.destination_repo:
            raise ValidationError('Origin and destination repositories must differ.')
        if self.origin_repo.variant_arch.arch != self.destination_repo.variant_arch.arch:
            raise ValidationError('Architecture for origin and destination repositories must NOT differ.')
        if self.origin_repo.service != self.destination_repo.service:
            raise ValidationError('Service for origin and destination repositories must NOT differ.')
        super(MultiDestination, self).clean()
