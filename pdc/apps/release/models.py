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
        RegexValidator(regex=r"^[a-z\-]+$", message='Only accept lowercase letter or -')])
    version             = models.CharField(max_length=200)
    name                = models.CharField(max_length=255)

    class Meta:
        unique_together = (
            ("short", "version"),
            ("name", "version"),
        )
        ordering = ("base_product_id", )

    def __unicode__(self):
        return u"%s-%s" % (self.short, self.version)

    def get_base_product_id(self):
        result = u"%s-%s" % (self.short.lower(), self.version)
        return result

    def export(self):
        return {
            "base_product_id": self.base_product_id,
            "short": self.short,
            "version": self.version,
            "name": self.name,
        }


@receiver(pre_save, sender=BaseProduct)
def populate_base_product_id(sender, instance, **kwargs):
    instance.base_product_id = instance.get_base_product_id()


class Product(models.Model):
    name    = models.CharField(max_length=200)
    short = models.CharField(max_length=200, unique=True, validators=[
        RegexValidator(regex=r"^[a-z\-]+$", message='Only accept lowercase letter or -')])

    def __unicode__(self):
        return self.short

    @property
    def active(self):
        releases = Release.objects.filter(active=True).filter(product_version__product=self)
        return bool(releases)

    @property
    def product_version_count(self):
        return ProductVersion.objects.filter(product=self).count()

    @property
    def active_product_version_count(self):
        return ProductVersion.objects.filter(product=self).filter(release__active=True).distinct().count()

    @property
    def release_count(self):
        return Release.objects.filter(product_version__product=self).count()

    @property
    def active_release_count(self):
        return Release.objects.filter(product_version__product=self).filter(active=True).distinct().count()

    def export(self):
        return {
            "name": self.name,
            "short": self.short,
        }


class ProductVersion(models.Model):
    name                = models.CharField(max_length=200)
    short = models.CharField(max_length=200, validators=[
        RegexValidator(regex=r"^[a-z\-]+$", message='Only accept lowercase letter or -')])
    version             = models.CharField(max_length=200)
    product             = models.ForeignKey(Product)
    product_version_id  = models.CharField(max_length=200)

    class Meta:
        unique_together = (("short", "version"))

    def __unicode__(self):
        return self.product_version_id

    @property
    def active(self):
        releases = Release.objects.filter(product_version=self).filter(active=True)
        return bool(releases)

    @property
    def release_count(self):
        return Release.objects.filter(product_version=self).count()

    @property
    def active_release_count(self):
        return Release.objects.filter(product_version=self).filter(active=True).count()

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
        RegexValidator(regex=r"^[a-z\-]+$", message='Only accept lowercase letter or -')])
    version             = models.CharField(max_length=200, blank=False)
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
        result = u"%s-%s" % (self.short.lower(), self.version)
        if self.base_product:
            result += u"-%s" % self.base_product.get_base_product_id()
        result += u"%s" % self.release_type.suffix
        return result

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
        If this variant is created from an integrated release, return a
        corresponding variant in the integrated release. Othwerwise, return
        None.
        """
        for release in self.release.integrated_releases.all():
            variants = release.variant_set.filter(variant_uid=self.variant_uid)
            if variants:
                return variants.first()
        return None

    @property
    def integrated_to(self):
        """
        If this variant belongs to an integrated release, return a
        corresponding variant in that release. Otherwise, return None.
        """
        integrated_to_release = self.release.integrated_with
        if not integrated_to_release:
            return None
        variants = integrated_to_release.variant_set.filter(variant_uid=self.variant_uid)
        return variants.first() if variants else None

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
        return u"%s.%s" % (self.variant, self.arch)
