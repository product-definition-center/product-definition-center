# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


from django.db import models

from pdc.apps.common.validators import validate_sigkey


def get_cached_id(cls, cache_field, value, create=False):
    """cached `value` to database `id`"""
    if not value:
        return None
    result = cls.CACHE.get(value, None)
    if result is None:
        if create:
            obj, _ = cls.objects.get_or_create(**{cache_field: value})
        else:
            obj = cls.objects.get(**{cache_field: value})
        cls.CACHE[value] = obj.id
        result = obj.id
    return result


class Arch(models.Model):
    name                = models.CharField(max_length=50, unique=True)

    class Meta:
        pass

    def __unicode__(self):
        return u"%s" % (self.name, )

    def export(self):
        # FIXME: export has been deprecated, use serializer instead.
        return {"name": self.name}


class SigKey(models.Model):
    key_id              = models.CharField(max_length=20, unique=True, validators=[validate_sigkey])
    name                = models.CharField(max_length=50, blank=True, null=True, unique=True)
    description         = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return u"%s" % self.key_id

    CACHE = {}

    @classmethod
    def get_cached_id(cls, value, create=False):
        """cached `key_id` to `id`"""
        return get_cached_id(cls, "key_id", value, create=create)

    def export(self):
        return {
            "key_id": self.key_id,
            "name": self.name,
            "description": self.description,
        }


class Label(models.Model):
    """
    Record label/tag with its name and description.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=500)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return u'%s' % self.name

    # FIXME: Compatible with ChangeSetMixin which still uses export funtion to record changeset
    def export(self, fields=None):
        _fields = ['name', 'description'] if fields is None else fields
        result = dict()
        if 'name' in _fields:
            result['name'] = self.name
        if 'description' in _fields:
            result['description'] = self.description
        return result
