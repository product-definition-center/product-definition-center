#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
from django.db import models
from pdc.apps.package.models import RPM


class UnreleasedVariant(models.Model):
    # Not the variant from compose ... which back references compose
    variant_id          = models.CharField(max_length=100, blank=False)
    variant_uid         = models.CharField(max_length=200, blank=False, unique=True)
    variant_name        = models.CharField(max_length=300, blank=False)
    variant_type        = models.CharField(max_length=100, blank=False)
    # variant_version/_release are _not_ distribution versions/releases
    variant_version     = models.CharField(max_length=100, blank=False)
    variant_release     = models.CharField(max_length=100, blank=False)
    # Default to '00000000' for now since this field will only be used once
    # other tooling is updated to supply this value. Eventually, this should
    # not have a default.
    variant_context     = models.CharField(max_length=100, blank=False, default='00000000')
    active              = models.BooleanField(default=False)
    koji_tag            = models.CharField(max_length=300, blank=False)
    modulemd            = models.TextField(blank=False)
    rpms                = models.ManyToManyField(RPM)

    class Meta:
        ordering = ("variant_name", "variant_version", "variant_release",
                    "variant_context")
        unique_together = (
            ("variant_name", "variant_version", "variant_release",
             "variant_context"),
        )

    def __unicode__(self):
        return u"%s" % (self.variant_uid, )

    def export(self):
        result = {
            'variant_id': self.variant_id,
            'variant_uid': self.variant_uid,
            'variant_name': self.variant_name,
            'variant_type': self.variant_type,
            'variant_version': self.variant_version,
            'variant_release': self.variant_release,
            'variant_context': self.variant_context,
            'active': self.active,
            'koji_tag': self.koji_tag,
            'modulemd': self.modulemd,
            'runtime_deps': [v.dependency for v in self.runtime_deps.all()],
            'build_deps': [v.dependency for v in self.build_deps.all()],
        }

        result["rpms"] = []
        objects = self.rpms.all()
        for obj in objects:
            result["rpms"].append(obj.export())

        return result


class VariantDependency(models.Model):

    dependency = models.CharField(max_length=300)
    stream = models.CharField(max_length=300)

    class Meta:
        abstract = True


class RuntimeDependency(VariantDependency):

    variant = models.ForeignKey("UnreleasedVariant",
                                related_name="runtime_deps")


class BuildDependency(VariantDependency):

    variant = models.ForeignKey("UnreleasedVariant",
                                related_name="build_deps")
