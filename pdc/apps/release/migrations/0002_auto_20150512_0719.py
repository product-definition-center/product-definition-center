# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


def create_release_types(apps, schema_editor):
    types = [
        {
            'suffix': '',
            'name': 'Release',
            'short': 'ga'
        },
        {
            'suffix': '-updates',
            'name': 'Updates for a release',
            'short': 'updates'
        },
        {
            'suffix': '-eus',
            'name': 'Extended Update Support (EUS)',
            'short': 'eus'
        },
        {
            'suffix': '-aus',
            'name': 'Advanced Update Support (AUS) (also Advanced Mission Critical, Long Life)',
            'short': 'aus'
        },
        {
            'suffix': '-els',
            'name': 'Extended Life-cycle Support',
            'short': 'els'
        },
        {
            'suffix': '-fast',
            'name': 'FasTrack',
            'short': 'fast'
        },
    ]
    ReleaseType = apps.get_model('release', 'ReleaseType')
    for type in types:
        ReleaseType.objects.create(**type)


def create_variant_types(apps, schema_editor):
    variants = [
        'variant',
        'optional',
        'addon',
        'layered-product',
    ]
    VariantType = apps.get_model('release', 'VariantType')
    for type in variants:
        VariantType.objects.create(name=type)


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_release_types),
        migrations.RunPython(create_variant_types),
    ]
