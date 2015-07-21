# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


from django.core.exceptions import ValidationError
from django.db import models

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


class ContentFormat(models.Model):
    # rpm, kickstart, iso
    name          = models.CharField(max_length=50, unique=True)
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
    service             = models.ForeignKey(Service)
    repo_family         = models.ForeignKey(RepoFamily)
    content_format      = models.ForeignKey(ContentFormat)
    content_category    = models.ForeignKey(ContentCategory)
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

    def clean(self):
        content_category = self.content_category.name
        if content_category == "debug" and "debug" not in self.name:
            raise ValidationError("Missing 'debug' in repo name '%s'" % self.name)
        if content_category != "debug" and "debug" in self.name:
            raise ValidationError("Found 'debug' in repo name '%s', but content category is '%s'"
                                  % (self.name, content_category))

        release_type = self.variant_arch.variant.release.release_type.short
        if release_type == "fast" and "-fast" not in self.name:
            raise ValidationError("Missing '-fast' in repo name '%s'" % self.name)
        if release_type != "fast" and "-fast" in self.name:
            raise ValidationError("Found '-fast' in repo name '%s', but release type is '%s'"
                                  % (self.name, release_type))

        if release_type == "eus" and ".z" not in self.name:
            raise ValidationError("Missing '.z' in repo name '%s'" % self.name)
        if release_type != "eus" and ".z" in self.name:
            raise ValidationError("Found '.z' in repo name '%s', but release type is '%s'"
                                  % (self.name, release_type))

        if release_type == "aus" and (".aus" not in self.name and ".ll" not in self.name):
            raise ValidationError("Missing '.aus' or '.ll' in repo name '%s'" % self.name)
        if release_type != "aus" and (".aus" in self.name or ".ll" in self.name):
            raise ValidationError("Found '.aus' or '.ll' in repo name '%s', but release type is '%s'"
                                  % (self.name, release_type))

        if release_type == "els" and "els" not in self.name:
            raise ValidationError("Missing 'els' in repo name '%s'" % self.name)
        if release_type != "els" and "els" in self.name:
            raise ValidationError("Found 'els' in repo name '%s', but release type is '%s'"
                                  % (self.name, release_type))

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
