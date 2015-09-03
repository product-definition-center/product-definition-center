#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db import models, connection, transaction
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.forms.models import model_to_dict

from pkg_resources import parse_version
from kobo.rpmlib import parse_nvra

from pdc.apps.common.models import get_cached_id
from pdc.apps.common.validators import validate_md5, validate_sha1, validate_sha256
from pdc.apps.common.hacks import add_returning
from pdc.apps.common.constants import ARCH_SRC
from pdc.apps.release.models import Release


class RPM(models.Model):
    name                = models.CharField(max_length=200, db_index=True)
    epoch               = models.PositiveIntegerField()
    version             = models.CharField(max_length=200, db_index=True)
    release             = models.CharField(max_length=200, db_index=True)
    arch                = models.CharField(max_length=200, db_index=True)  # nosrc
    srpm_name           = models.CharField(max_length=200, db_index=True)  # package (name of srpm)
    srpm_nevra          = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    # Well behaved filenames are unique, but that is enforced by having unique NVRA.
    filename            = models.CharField(max_length=4096)
    linked_releases     = models.ManyToManyField('release.Release', related_name='linked_rpms')

    class Meta:
        unique_together = (
            ("name", "epoch", "version", "release", "arch"),
        )

    def __unicode__(self):
        return u"%s.rpm" % self.nevra

    def linked_composes(self):
        from pdc.apps.compose.models import Compose
        """Return a set of all composes that this RPM is linked"""
        return Compose.objects.filter(variant__variantarch__composerpm__rpm=self).distinct()

    @property
    def nevra(self):
        return u"%s-%s:%s-%s.%s" % (self.name, self.epoch, self.version, self.release, self.arch)

    @staticmethod
    def check_srpm_nevra(srpm_nevra, arch):
        #  srpm_nevra should be empty if and only if arch is src.
        if (arch == ARCH_SRC) == bool(srpm_nevra):
            raise ValidationError("RPM's srpm_nevra should be empty if and only if arch is src")

    def export(self, fields=None):
        _fields = set(['name', 'epoch', 'version', 'release', 'arch',
                       'srpm_name', 'srpm_nevra', 'linked_releases']) if fields is None else set(fields)
        result = model_to_dict(self, fields=_fields - {'linked_releases'})
        if 'linked_releases' in _fields:
            result['linked_releases'] = []
            for linked_release in self.linked_releases.all():
                result['linked_releases'].append(linked_release.release_id)
        return result

    @staticmethod
    def default_filename(data):
        """
        Create default file name based on name, version, release and arch. If
        the data does not contain all these values, None is returned.
        """
        try:
            return '{name}-{version}-{release}.{arch}.rpm'.format(**data)
        except KeyError:
            return None

    def save(self, *args, **kwargs):
        self.check_srpm_nevra(self.srpm_nevra, self.arch)
        super(RPM, self).save(*args, **kwargs)

    @staticmethod
    def bulk_insert(cursor, rpm_nevra, filename, srpm_nevra=None):
        nvra = parse_nvra(rpm_nevra)
        if srpm_nevra:
            srpm_name = parse_nvra(srpm_nevra)["name"]
        else:
            srpm_name = nvra["name"]

        sql = add_returning("""INSERT INTO %s (name, epoch, version, release, arch, srpm_nevra, srpm_name, filename)
                               VALUES (%%s, %%s, %%s, %%s, %%s, %%s, %%s, %%s)""" % RPM._meta.db_table)

        try:
            sid = transaction.savepoint()
            RPM.check_srpm_nevra(rpm_nevra, srpm_nevra)
            cursor.execute(sql, [nvra["name"], nvra["epoch"], nvra["version"], nvra["release"],
                                 nvra["arch"], srpm_nevra, srpm_name, filename])
            if connection.features.can_return_id_from_insert:
                insert_id = connection.ops.fetch_returned_insert_id(cursor)
            else:
                insert_id = connection.ops.last_insert_id(cursor, RPM._meta.db_table, "id")
        except (IntegrityError, ValidationError):
            transaction.savepoint_rollback(sid)
            cursor.execute("""SELECT %s FROM %s WHERE name=%%s AND epoch=%%s AND
                              version=%%s and release=%%s AND arch=%%s""" % ("id", RPM._meta.db_table),
                           [nvra["name"], nvra["epoch"], nvra["version"], nvra["release"], nvra["arch"]])
            insert_id = int(cursor.fetchone()[0])
        transaction.savepoint_commit(sid)
        return insert_id

    @property
    def sort_key(self):
        return (self.epoch, parse_version(self.version), parse_version(self.release))


class ImageFormat(models.Model):
    name                = models.CharField(max_length=30, db_index=True, unique=True)

    def __unicode__(self):
        return u"%s" % self.name

    CACHE = {}

    @classmethod
    def get_cached_id(cls, value):
        """cached `name` to `id`"""
        return get_cached_id(cls, "name", value)


class ImageType(models.Model):
    name                = models.CharField(max_length=30, db_index=True, unique=True)

    def __unicode__(self):
        return u"%s" % self.name

    CACHE = {}

    @classmethod
    def get_cached_id(cls, value):
        """cached `name` to `id`"""
        return get_cached_id(cls, "name", value)


class Image(models.Model):
    file_name           = models.CharField(max_length=200, db_index=True)
    image_format        = models.ForeignKey(ImageFormat)
    image_type          = models.ForeignKey(ImageType)
    disc_number         = models.PositiveIntegerField()
    disc_count          = models.PositiveIntegerField()
    arch                = models.CharField(max_length=200, db_index=True)

    mtime               = models.BigIntegerField()
    size                = models.BigIntegerField()

    bootable            = models.BooleanField(default=False)
    implant_md5         = models.CharField(max_length=32)

    volume_id           = models.CharField(max_length=32, null=True, blank=True)

    # TODO: move checksums to a different table? need at least one manadatory checksum to identify ISOs
    md5                 = models.CharField(max_length=32, null=True, blank=True, validators=[validate_md5])
    sha1                = models.CharField(max_length=40, null=True, blank=True, validators=[validate_sha1])
    sha256              = models.CharField(max_length=64, validators=[validate_sha256])

    class Meta:
        unique_together = (
            ("file_name", "sha256"),
        )

    def __unicode__(self):
        return u"%s" % self.file_name

    def composes(self):
        """Return a set of all composes that this image belongs to."""
        return set([ci.variant_arch.variant.compose for ci in self.composeimage_set.all()])


class Archive(models.Model):
    build_nvr           = models.CharField(max_length=200, db_index=True)
    name                = models.CharField(max_length=200, db_index=True)

    size                = models.BigIntegerField()
    md5                 = models.CharField(max_length=32, validators=[validate_md5])

    class Meta:
        unique_together = (
            ('build_nvr', 'name', 'md5'),
        )

    def __unicode__(self):
        return u"%s" % self.name

    def export(self, fields=None):
        _fields = ['build_nvr', 'name', 'size', 'md5'] if fields is None else fields
        return model_to_dict(self, fields=_fields)


class BuildImage(models.Model):
    image_id            = models.CharField(max_length=200, unique=True, db_index=True)
    image_format        = models.ForeignKey(ImageFormat)
    md5                 = models.CharField(max_length=32, validators=[validate_md5])

    rpms                = models.ManyToManyField(RPM)
    archives            = models.ManyToManyField(Archive)
    releases            = models.ManyToManyField(Release)

    def __unicode__(self):
        return u"%s" % self.image_id

    def export(self, fields=None):
        _fields = ['image_id', 'image_format', 'md5',
                   'rpms', 'archives', 'releases'] if fields is None else fields
        result = dict()
        if 'image_id' in _fields:
            result['image_id'] = self.image_id
        if 'md5' in _fields:
            result['md5'] = self.md5
        if 'image_format' in _fields:
            result['image_format'] = self.image_format.name

        for field in ('rpms', 'archives', 'releases'):
            if field in _fields:
                result[field] = []
                objects = getattr(self, field).all()
                for obj in objects:
                    result[field].append(obj.export())

        return result
