#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.db import models, connection, transaction
from django.db.utils import IntegrityError

from pdc.apps.common import models as common_models
from pdc.apps.common.hacks import add_returning

from productmd import composeinfo


class ComposeType(models.Model):
    name                = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return u"%s" % self.name


class ComposeAcceptanceTestingState(models.Model):
    name                = models.CharField(max_length=200, unique=True)

    @staticmethod
    def get_untested():
        """Return default acceptance testing status."""
        return ComposeAcceptanceTestingState.objects.get(name='untested').pk

    def __unicode__(self):
        return u"%s" % self.name


class Compose(models.Model):
    release             = models.ForeignKey("release.Release")
    compose_id          = models.CharField(max_length=200, unique=True)
    compose_date        = models.DateField()
    compose_type        = models.ForeignKey(ComposeType)
    compose_respin      = models.PositiveIntegerField()
    compose_label       = models.CharField(max_length=200, null=True, blank=True)
    dt_imported         = models.DateTimeField(auto_now_add=True)
    deleted             = models.BooleanField(default=False)
    acceptance_testing  = models.ForeignKey(ComposeAcceptanceTestingState,
                                            default=ComposeAcceptanceTestingState.get_untested)
    linked_releases     = models.ManyToManyField('release.Release', related_name='linked_composes', blank=True)

    class Meta:
        unique_together = (
            ("release", "compose_label"),
            ("release", "compose_date", "compose_type", "compose_respin"),
        )

    def __unicode__(self):
        if self.compose_label:
            return u"%s (%s)" % (self.compose_id, self.compose_label)
        return u"%s" % self.compose_id

    def export(self):
        return {
            "id": self.id,
            "compose_id": self.compose_id,
        }

    def __cmp__(self, another):
        """
        If both composes belong to the same release, they are compared by
        productmd. Otherwise they inherit the order from releases.
        """
        if self.release == another.release:
            return cmp(self._get_compose_info(), another._get_compose_info())
        return cmp(self.release.version_sort_key(), another.release.version_sort_key())

    def _get_compose_info(self):
        if not hasattr(self, '_compose_info'):
            self._compose_info = composeinfo.Compose(None)
            self._compose_info.id = self.compose_id
            self._compose_info.date = self.compose_date
            self._compose_info.respin = self.compose_respin
            self._compose_info.type = self.compose_type.name
        return self._compose_info

    @property
    def sigkeys(self):
        """
        Get a list of sigkey ids used in the compose.
        """
        sigkeys = common_models.SigKey.objects.filter(composerpm__variant_arch__variant__compose=self).distinct()
        result = sorted([i.key_id for i in sigkeys])
        if ComposeRPM.objects.filter(variant_arch__variant__compose=self, sigkey=None).exists():
            # detect unsigned RPMs
            result.append(None)
        return result

    def get_rpm_mapping(self, package, disable_overrides=False, release=None):
        """
        Get RPM mapping for this compose. This method returns a tuple. First
        element is the following mapping:

        {
            variant: {
                arch: {
                    rpm_name: [
                        {
                            arch: {
                                included: bool,
                                override: str
                            }
                        }
                    ]
                }
            }
        }

        Override tag is either 'orig' (ComposeRPM existed, no corresponding
        override), 'delete' (ComposeRPM exists, corresponding override excludes
        it) or 'create' (no ComposeRPM, include override).

        Included is False for not included packages, True otherwise.

        The second element of the tuple is a list of overrides that exclude
        non-existent package or include already existing package. All the
        overrides in this list have do_not_delete set. All overrides that could
        be in this list but can be deleted actually are deleted.

        If `release` argument is not specified, the release for which the
        compose was built will be used. The overrides will be taken from this
        release as well as variants and arches.
        """
        release = release or self.release
        mapping = ComposeRPMMapping()
        mapping.load_from_compose(self, package, release)
        overrides = OverrideRPM.objects.filter(release=release).filter(srpm_name=package)
        useless_overrides = []
        if not disable_overrides:
            useless_overrides = mapping.apply_overrides(overrides)

        return (mapping, useless_overrides)

    def get_rpms(self, rpm_name):
        """
        Find all RPMs with given name associated with this compose.
        """
        from pdc.apps.package.models import RPM
        return (RPM.objects.filter(name=rpm_name)
                .filter(composerpm__variant_arch__variant__compose=self)
                .distinct())

    def get_arch_testing_status(self):
        """
        Get a mapping of all variant.archs to their testing status.
        """
        result = {}
        for var_arch in VariantArch.objects.filter(variant__compose=self):
            variant = result.setdefault(var_arch.variant.variant_uid, {})
            variant[var_arch.arch.name] = var_arch.rtt_testing_status.name
        return result


def find_by(list, key, val):
    """Find a dict with given key=val pair in a list."""
    matches = [i for i in list if i[key] == val]
    return matches[0] if len(matches) == 1 else None


# This is duplicate by design
# these variants are a snapshot of real compose content
# -> no direct relation to release variants
class Variant(models.Model):
    compose             = models.ForeignKey(Compose)
    variant_id          = models.CharField(max_length=100, blank=False)
    variant_uid         = models.CharField(max_length=200, blank=False)
    variant_name        = models.CharField(max_length=300, blank=False)
    variant_type        = models.ForeignKey("release.VariantType", related_name="compose_variant")
    deleted             = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ("compose", "variant_uid"),
        )
        ordering = ("variant_uid", )

    def __unicode__(self):
        return u"%s" % (self.variant_uid, )

    @property
    def arches(self):
        return [i.arch for i in self.variantarch_set.all()]

    def export(self):
        return {
            'compose': self.compose.compose_id,
            'variant_id': self.variant_id,
            'variant_uid': self.variant_uid,
            'variant_name': self.variant_name,
            'variant_type': self.variant_type.name,
            'arches': [arch.name for arch in self.arches],
        }


class VariantArch(models.Model):
    variant             = models.ForeignKey(Variant)
    arch                = models.ForeignKey("common.Arch", related_name="+")
    rtt_testing_status  = models.ForeignKey(ComposeAcceptanceTestingState,
                                            default=ComposeAcceptanceTestingState.get_untested)
    deleted             = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ("variant", "arch"),
        )
        ordering = ("variant", "arch")

    def __unicode__(self):
        return u"%s.%s" % (self.variant, self.arch)


class Path(models.Model):
    """
    Class representing a path in compose. The same path can be reused in
    multiple places (e.g. in more RPMs).
    """
    path = models.CharField(max_length=4096, unique=True, blank=True)

    def __unicode__(self):
        return unicode(self.path)

    CACHE = {}

    @classmethod
    def get_cached_id(cls, value, create=False):
        return common_models.get_cached_id(cls, 'path', value, create)


class ComposeRPMManager(models.Manager):
    def get_queryset(self):
        return super(ComposeRPMManager, self).get_queryset().select_related("rpm", "sigkey", "content_category")


class ComposeRPM(models.Model):
    variant_arch        = models.ForeignKey(VariantArch, db_index=True)
    rpm                 = models.ForeignKey("package.RPM", db_index=True)
    sigkey              = models.ForeignKey("common.SigKey", null=True, blank=True)
    content_category    = models.ForeignKey("repository.ContentCategory")
    path                = models.ForeignKey(Path)

    objects = ComposeRPMManager()

    class Meta:
        unique_together = (
            ("variant_arch", "rpm"),
        )

    def __unicode__(self):
        return u"%s/%s/%s" % (self.variant_arch.variant.compose.compose_id, self.variant_arch, self.rpm)

    @staticmethod
    def bulk_insert(cursor, variant_arch_id, rpm_id, content_category_id, sigkey_id, path_id):
        sql = add_returning("""INSERT INTO %s (variant_arch_id, rpm_id, sigkey_id, content_category_id, path_id)
                               VALUES (%%s, %%s, %%s, %%s, %%s)""" % ComposeRPM._meta.db_table)

        try:
            sid = transaction.savepoint()
            cursor.execute(sql, [variant_arch_id, rpm_id, sigkey_id, content_category_id, path_id])
            if connection.features.can_return_id_from_insert:
                insert_id = connection.ops.fetch_returned_insert_id(cursor)
            else:
                insert_id = connection.ops.last_insert_id(cursor, ComposeRPM._meta.db_table, "id")
        except IntegrityError:
            transaction.savepoint_rollback(sid)
            cursor.execute("SELECT %s FROM %s WHERE variant_arch_id=%%s AND rpm_id=%%s"
                           % ("id", ComposeRPM._meta.db_table),
                           [variant_arch_id, rpm_id])
            insert_id = int(cursor.fetchone()[0])
        transaction.savepoint_commit(sid)
        return insert_id


class ComposeRPMMapping(object):
    def __init__(self, data=None):
        self.data = data or {}
        self.compose = None
        self.package = None

    def add_rpm(self, variant, arch, rpm_name, rpm_arch):
        self.data.setdefault(variant, {}) \
                 .setdefault(arch, {}) \
                 .setdefault(rpm_name, []) \
                 .append(rpm_arch)

    def load_from_compose(self, compose, package, release):
        self.compose = compose
        self.package = package

        release_variants = {}
        for variant in release.variant_set.all():
            release_variants[variant.variant_uid] = set(variant.arches)

        for crpm in ComposeRPM.objects.filter(rpm__srpm_name=package,
                                              variant_arch__variant__compose=compose).select_related():
            variant = crpm.variant_arch.variant.variant_uid
            arch    = crpm.variant_arch.arch.name
            if arch not in release_variants.get(variant, set()):
                continue
            self.add_rpm(variant,
                         arch,
                         crpm.rpm.name,
                         {'rpm_arch': crpm.rpm.arch, 'included': True, 'override': 'orig'})

    def get_rpm_dict(self, variant, arch):
        return self.data.setdefault(variant, {}).setdefault(arch, {})

    def _process_unused(self, override, useless_overrides, to_be_deleted):
        if override.do_not_delete:
            useless_overrides.append(override)
        else:
            to_be_deleted.append(override)

    def apply_overrides(self, overrides, do_delete=True):
        tbd = []
        useless_overrides = []
        for override in overrides:
            rpm_dict = self.get_rpm_dict(override.variant, override.arch)
            if override.rpm_name in rpm_dict:
                # existing rpm name
                rpm = find_by(rpm_dict[override.rpm_name], 'rpm_arch', override.rpm_arch)
                if rpm:
                    if not override.include:
                        # existing arch
                        rpm['included'] = False
                        rpm['override'] = 'delete'
                    else:
                        self._process_unused(override, useless_overrides, tbd)
                else:
                    # not existing arch
                    if override.include:
                        rpm = {'rpm_arch': override.rpm_arch, 'included': override.include, 'override': 'create'}
                        rpm_dict[override.rpm_name].append(rpm)
                    else:
                        self._process_unused(override, useless_overrides, tbd)
            else:
                # new rpm name
                if override.include:
                    rpm = {'rpm_arch': override.rpm_arch, 'included': override.include, 'override': 'create'}
                    rpm_dict[override.rpm_name] = [rpm]
                else:
                    self._process_unused(override, useless_overrides, tbd)

        if do_delete:
            for override in tbd:
                print ' *** NOTICE: deleted override %s' % override
                override.delete()

        return useless_overrides

    def get_pure_dict(self):
        result = {}
        for variant, arch, rpm_name, rpm_data in self:
            if isinstance(rpm_data, basestring):
                result.setdefault(variant, {}).setdefault(arch, {}).setdefault(rpm_name, [])
                result[variant][arch][rpm_name].append(rpm_data)
            elif rpm_data['included']:
                result.setdefault(variant, {}).setdefault(arch, {}).setdefault(rpm_name, [])
                result[variant][arch][rpm_name].append(rpm_data['rpm_arch'])
        return result

    def __iter__(self):
        for variant in sorted(self.data):
            for arch in sorted(self.data[variant]):
                for rpm_name in sorted(self.data[variant][arch]):
                    for rpm_data in sorted(self.data[variant][arch][rpm_name],
                                           key=lambda x: x['rpm_arch'] if isinstance(x, dict) else x):
                        yield (variant, arch, rpm_name, rpm_data)

    def compute_changes(self, new_mapping):
        """
        Compute differences between current mapping and new mapping and return
        a list of actions suitable for OverrideRPM.update_object.

        The overrides to be created have do_not_delete set to False and no
        comment.
        """
        changes = []

        def stage(type, args, include, changes=changes):
            data = {'release_id': self.compose.release.release_id,
                    'srpm_name': self.package,
                    'action': type,
                    'variant': args['variant'],
                    'arch': args['arch'],
                    'rpm_name': args['rpm_name'],
                    'rpm_arch': args['rpm_arch'],
                    'include': include,
                    }
            changes.append(data)

        for (variant, arch, rpm_name, rpm_arch) in new_mapping:
            try:
                old_archs = self.data[variant][arch][rpm_name]
            except KeyError:
                old_archs = []
            tmp_arch = find_by(old_archs, 'rpm_arch', rpm_arch)
            if not tmp_arch:    # Completely new mapping
                stage('create',
                      {'variant': variant, 'arch': arch, 'rpm_name': rpm_name, 'rpm_arch': rpm_arch}, True)
            elif not tmp_arch['included']:  # Disabling of existing exclude override
                stage('delete',
                      {'variant': variant, 'arch': arch, 'rpm_name': rpm_name, 'rpm_arch': rpm_arch}, False)

        for (variant, arch, rpm_name, data) in self:
            if not data['included']:    # Excluded RPM, ignore
                continue
            try:
                new_archs = new_mapping.data[variant][arch][rpm_name]
            except KeyError:
                new_archs = []
            if data['rpm_arch'] in new_archs:   # RPM present in new mapping
                continue
            if data['override'] == 'create':    # Remove include override
                stage('delete',
                      {'variant': variant, 'arch': arch, 'rpm_name': rpm_name, 'rpm_arch': data['rpm_arch']}, True)
            else:
                stage('create',
                      {'variant': variant, 'arch': arch, 'rpm_name': rpm_name, 'rpm_arch': data['rpm_arch']}, False)

        return changes


class OverrideRPM(models.Model):
    """To add/disable RPMs for a release"""
    release             = models.ForeignKey("release.Release")
    variant             = models.CharField(max_length=200)
    arch                = models.CharField(max_length=20)
    srpm_name           = models.CharField(max_length=200)  # srpm_name = package; needed for grouping with ComposeRPMs
    rpm_name            = models.CharField(max_length=200)
    rpm_arch            = models.CharField(max_length=20)

    # include / exclude from mappings
    include             = models.BooleanField(default=True)

    # if an override should not be deleted, specify reason in the comment field
    comment             = models.CharField(max_length=200, blank=True)
    do_not_delete       = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            ("release", "variant", "arch", "rpm_name", "rpm_arch"),
        )

    def __unicode__(self):
        include = self.include and "+" or "-"
        return u"[%s] %s.%s %s.%s %s" % (self.release, self.variant, self.arch, self.rpm_name, self.rpm_arch, include)

    def export(self):
        return {
            "release_id": self.release.release_id,
            "variant": self.variant,
            "arch": self.arch,
            "srpm_name": self.srpm_name,
            "rpm_name": self.rpm_name,
            "rpm_arch": self.rpm_arch,
            "include": self.include,
            "comment": self.comment,
            "do_not_delete": self.do_not_delete,
        }

    @classmethod
    def update_object(klass, action, release, data):
        """
        Given a dict describing a change in overrides, perform the changes.
        Returns a triple (pk, old_value, new_value) of changed override.
        """
        orpm, created = klass.objects.get_or_create(release=release,
                                                    variant=data['variant'],
                                                    arch=data['arch'],
                                                    rpm_name=data['rpm_name'],
                                                    rpm_arch=data['rpm_arch'],
                                                    srpm_name=data['srpm_name'])
        pk = orpm.pk
        old_val = 'null' if created else orpm.export()
        if action == 'create':
            orpm.do_not_delete = data.get('do_not_delete', False)
            orpm.comment = data.get('comment', '')
            orpm.include = data['include']
            orpm.save()
            new_val = orpm.export()
        elif action == 'delete':
            new_dnd = data.get('do_not_delete', False)
            if not new_dnd:
                orpm.delete()
                new_val = 'null'
            else:
                orpm.do_not_delete = True
                orpm.comment = data.get('comment', '')
                orpm.include = not data['include']
                orpm.save()
                new_val = orpm.export()
        return pk, old_val, new_val


class ComposeImage(models.Model):
    variant_arch        = models.ForeignKey(VariantArch, db_index=True)
    image               = models.ForeignKey("package.Image", db_index=True)
    path                = models.ForeignKey(Path)

    class Meta:
        unique_together = (
            ("variant_arch", "image"),
        )


class Location(models.Model):
    name = models.CharField(max_length=50)
    short = models.CharField(max_length=50, unique=True)


class Scheme(models.Model):
    name = models.CharField(max_length=50, unique=True)


class ComposeTree(models.Model):
    compose             = models.ForeignKey("Compose")
    variant             = models.ForeignKey("Variant")
    arch                = models.ForeignKey("common.Arch")
    location            = models.ForeignKey("Location")
    scheme              = models.ForeignKey("Scheme")
    url                 = models.CharField(max_length=255)
    synced_content      = models.ManyToManyField('repository.ContentCategory')

    class Meta:
        unique_together = (
            ("compose", "variant", "arch", "location"),
        )

    def __unicode__(self):
        return u"%s-%s-%s-%s" % (self.compose, self.variant, self.arch, self.location)

    def export(self):
        return {
            "compose": self.compose.compose_id,
            "variant": self.variant.variant_uid,
            "arch": self.arch.name,
            "location": self.location.short,
            "scheme": self.scheme.name,
            "url": self.url,
            "synced_content": [item.name for item in self.synced_content.all()]
        }
