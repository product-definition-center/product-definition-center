# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import json

from django.db import models
from django.core.validators import RegexValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from productmd.common import RELEASE_SHORT_RE, RELEASE_VERSION_RE
from productmd.common import create_release_id

from pdc.apps.common.hacks import as_list
from . import signals


class ReleaseType(models.Model):
    short               = models.CharField(max_length=255, blank=False, unique=True)
    name                = models.CharField(max_length=255, blank=False, unique=True)
    suffix              = models.CharField(max_length=255, blank=True, unique=True)

    def __unicode__(self):
        return u"%s" % self.short


class BaseProduct(models.Model):
    # base_product_id is populated by populate_base_product_id() pre_save hook
    base_product_id     = models.CharField(max_length=200, blank=False, unique=True)
    short = models.CharField(max_length=200, validators=[
        RegexValidator(regex=RELEASE_SHORT_RE.pattern, message='Only accept lowercase letters, numbers or -')])
    version             = models.CharField(max_length=200)
    name                = models.CharField(max_length=255)
    release_type        = models.ForeignKey(ReleaseType, blank=False, db_index=True)

    class Meta:
        unique_together = (
            ("short", "version", "release_type"),
            ("name", "version", "release_type"),
        )
        ordering = ("base_product_id", )

    def __unicode__(self):
        return unicode(self.base_product_id)

    def get_base_product_id(self):
        return create_release_id(self.short.lower(), self.version, self.release_type.short)

    def export(self):
        return {
            "base_product_id": self.base_product_id,
            "short": self.short,
            "version": self.version,
            "name": self.name,
            "release_type": self.release_type.short,
        }


@receiver(pre_save, sender=BaseProduct)
def populate_base_product_id(sender, instance, **kwargs):
    instance.base_product_id = instance.get_base_product_id()


class Product(models.Model):
    name    = models.CharField(max_length=200)
    short = models.CharField(max_length=200, unique=True, validators=[
        RegexValidator(regex=RELEASE_SHORT_RE.pattern, message='Only accept lowercase letters, numbers or -')])

    class Meta:
        ordering = ("short", )

    def __unicode__(self):
        return self.short

    @property
    def active(self):
        return self.active_release_count > 0

    @property
    def product_version_count(self):
        return self.productversion_set.count()

    @property
    def active_product_version_count(self):
        return sum(1 for pv in self.productversion_set.all() if pv.active)

    @property
    def release_count(self):
        return sum(pv.release_count for pv in self.productversion_set.all())

    @property
    def active_release_count(self):
        return sum(pv.active_release_count for pv in self.productversion_set.all())

    def export(self):
        return {
            "name": self.name,
            "short": self.short,
        }


class ProductVersion(models.Model):
    name                = models.CharField(max_length=200)
    short = models.CharField(max_length=200, validators=[
        RegexValidator(regex=RELEASE_SHORT_RE.pattern, message='Only accept lowercase letters, numbers or -')])
    version             = models.CharField(max_length=200, validators=[
        RegexValidator(regex=RELEASE_VERSION_RE.pattern, message='Only accept comma separated numbers or any text')])
    product             = models.ForeignKey(Product)
    product_version_id  = models.CharField(max_length=200)

    class Meta:
        unique_together = (("short", "version"))
        ordering = ("product_version_id", )

    def __unicode__(self):
        return self.product_version_id

    @property
    def active(self):
        return self.active_release_count > 0

    @property
    def release_count(self):
        return self.release_set.count()

    @property
    def active_release_count(self):
        return sum(1 for r in self.release_set.all() if r.active)

    def get_product_version_id(self):
        return u"%s-%s" % (self.short.lower(), self.version)

    def export(self):
        return {
            "name": self.name,
            "short": self.short,
            "version": self.version,
            "product_version_id": self.product_version_id,
            "product": self.product and self.product.short or None
        }


@receiver(pre_save, sender=ProductVersion)
def populate_product_version_id(sender, instance, **kwargs):
    instance.product_version_id = instance.get_product_version_id()


class Release(models.Model):
    # release_id is populated by populate_release_id() pre_save hook
    release_id          = models.CharField(max_length=200, blank=False, unique=True)
    short = models.CharField(max_length=200, blank=False, validators=[
        RegexValidator(regex=RELEASE_SHORT_RE.pattern, message='Only accept lowercase letters, numbers or -')])
    version             = models.CharField(max_length=200, blank=False, validators=[
        RegexValidator(regex=RELEASE_VERSION_RE.pattern, message='Only accept comma separated numbers or any text')])
    name                = models.CharField(max_length=255, blank=False)
    release_type        = models.ForeignKey(ReleaseType, blank=False, db_index=True)
    base_product        = models.ForeignKey(BaseProduct, null=True, blank=True)
    active              = models.BooleanField(default=True)
    product_version     = models.ForeignKey(ProductVersion, blank=True, null=True)
    integrated_with     = models.ForeignKey('self',
                                            null=True,
                                            blank=True,
                                            related_name='integrated_releases')

    class Meta:
        unique_together = (
            ("short", "version", "release_type", "base_product"),
        )
        ordering = ("release_id", )

    def __unicode__(self):
        return u"%s" % self.release_id

    def is_active(self):
        return self.active is True

    def get_release_id(self):
        bp_dict = {}
        if self.base_product:
            bp_dict = {
                "bp_short": self.base_product.short.lower(),
                "bp_version": self.base_product.version,
                "bp_type": self.base_product.release_type.short,
            }
        return create_release_id(self.short.lower(), self.version, self.release_type.short, **bp_dict)

    def export(self):
        result = {
            "release_id": self.release_id,
            "short": self.short,
            "version": self.version,
            "name": self.name,
            "release_type": self.release_type.short,
            "active": self.active,
            "product_version": (self.product_version.product_version_id
                                if self.product_version else None),
            "integrated_with": (self.integrated_with.release_id
                                if self.integrated_with else None),
        }
        if self.base_product:
            result["base_product"] = self.base_product.base_product_id
        else:
            result["base_product"] = None
        return result

    def get_all_composes(self):
        """
        Return a set of all composes built for this release or linked to it.
        """
        return set(self.compose_set.all()) | set(self.linked_composes.all())

    def get_latest_compose(self):
        """
        Find latest compose for this release. If there are no composes, this
        function returns `None`.
        """
        composes = sorted(self.get_all_composes())
        if not composes:
            return None
        return composes[-1]

    @property
    def trees(self):
        """
        Return a set of Variant.Arch pairs in this release.
        """
        trees = set()
        for variant in self.variant_set.all():
            for arch in variant.arches:
                trees.add('%s.%s' % (variant.variant_uid, arch))
        return trees

    def version_sort_key(self):
        """
        Get a list used for sorting by version: first element will be short
        name, followed by numeric components of the version. If the version is
        not in the form of X.Y..., the result will make no sense for ordering,
        but it should not crash.
        """
        try:
            return [self.short] + [int(x) for x in self.version.split('.')]
        except ValueError:
            return [self.short]

    @property
    def integrated_release_variants(self):
        """
        Returns mapping from Variant-UID to release instance from which the
        variant is integrated.
        """
        if not hasattr(self, '_integrated_release_variants'):
            self._integrated_release_variants = {}
            for release in self.integrated_releases.all():
                for variant in release.variant_set.all():
                    self._integrated_release_variants[variant.variant_uid] = release
        return self._integrated_release_variants


@receiver(pre_save, sender=Release)
def populate_release_id(sender, instance, **kwargs):
    instance.release_id = instance.get_release_id()


class VariantType(models.Model):
    name                = models.CharField(max_length=100, blank=False)

    def __unicode__(self):
        return u"%s" % (self.name, )


class Variant(models.Model):
    release             = models.ForeignKey(Release)
    variant_id          = models.CharField(max_length=100, blank=False)
    variant_uid         = models.CharField(max_length=200, blank=False)
    variant_name        = models.CharField(max_length=300, blank=False)
    variant_type        = models.ForeignKey(VariantType)
    deleted             = models.BooleanField(default=False)
    # These are to optionally override variant_version/_release in
    # tree.UnreleasedVariant. They are _not_ distribution versions/releases.
    variant_version     = models.CharField(max_length=100, blank=True,
                                           null=True)
    variant_release     = models.CharField(max_length=100, blank=True,
                                           null=True)

    class Meta:
        unique_together = (
            ("release", "variant_uid"),
        )
        ordering = ("variant_uid", )

    def __unicode__(self):
        return u"%s" % (self.variant_uid, )

    @property
    def arches(self):
        return sorted([i.arch.name for i in self.variantarch_set.all()])

    @property
    def integrated_from(self):
        """
        If this variant is created from an integrated release, return the
        integrated release. Othwerwise, return None.
        """
        return self.release.integrated_release_variants.get(self.variant_uid)

    @property
    def integrated_to(self):
        """
        If this variant belongs to an integrated release, return that release.
        Otherwise, return None.
        """
        return self.release.integrated_with

    def export(self):
        return {
            'release': self.release.release_id,
            'variant_id': self.variant_id,
            'variant_uid': self.variant_uid,
            'variant_name': self.variant_name,
            'variant_type': self.variant_type.name,
            'arches': self.arches,
        }


@receiver(signals.release_clone)
def clone_variants(sender, request, original_release, release, **kwargs):
    """
    Clone all variants and arches from `original_release` to new instance. All
    newly created objects are logged into a changeset. Since nor Variant nor
    VariantArch has an export method, their string representation is used
    instead.
    """
    filter_include_trees = 'include_trees' in request.data
    variant_mapping = {}
    for tree in as_list(request.data.get('include_trees', []), 'include_trees'):
        try:
            variant, arch = tree.split('.')
        except ValueError:
            raise ValidationError('%s is not a well-formed tree specifier.' % tree)
        if tree not in original_release.trees:
            raise ValidationError('%s is not in release %s.' % (tree, original_release))
        variant_mapping.setdefault(variant, set()).add(arch)

    for variant in original_release.variant_set.all():
        if filter_include_trees and variant.variant_uid not in variant_mapping:
            continue
        archs = variant.variantarch_set.all()
        variant.pk = None
        variant.release = release
        variant.save()
        request.changeset.add('Variant', variant.pk,
                              'null', json.dumps(str(variant)))
        for variant_arch in archs:
            if filter_include_trees and variant_arch.arch.name not in variant_mapping[variant.variant_uid]:
                continue
            variant_arch.pk = None
            variant_arch.variant = variant
            variant_arch.save()
            request.changeset.add('VariantArch', variant_arch.pk,
                                  'null', json.dumps(str(variant_arch)))


class VariantArch(models.Model):
    variant             = models.ForeignKey(Variant)
    arch                = models.ForeignKey("common.Arch")
    deleted             = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ("variant", "arch"),
        )
        ordering = ("variant", "arch")

    def __unicode__(self):
        return u"%s.%s, deleted: %s" % (self.variant, self.arch, self.deleted)


class ReleaseGroupType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return u"%s" % self.name


class ReleaseGroup(models.Model):
    name                = models.CharField(max_length=255, blank=False, unique=True)
    description         = models.CharField(max_length=255, blank=False)
    type                = models.ForeignKey(ReleaseGroupType)
    releases            = models.ManyToManyField(Release, blank=True)
    active              = models.BooleanField(default=True)

    class Meta:
        ordering = ("name", )

    def __unicode__(self):
        return u"%s" % self.name

    def export(self, fields=None):
        _fields = ['name', 'description', 'type', 'releases', 'active'] if fields is None else fields
        result = dict()
        for field in ('name', 'description', 'active'):
            if field in _fields:
                result[field] = getattr(self, field)
        if 'releases' in _fields:
            result['releases'] = []
            releases = self.releases.all()
            for obj in releases:
                    result['releases'].append(obj.export())
        if 'type' in _fields:
            result['type'] = self.type.name
        return result
