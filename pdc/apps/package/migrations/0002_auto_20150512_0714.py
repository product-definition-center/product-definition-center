# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


def create_image_formats(apps, schema_editor):
    formats = [
        'iso',
        'qcow',
        'qcow2',
        'raw',
        'rhevm.ova',
        'sda.raw',
        'vdi',
        'vmdk',
        'vmx',
        'vsphere.ova',
        'docker',
    ]
    ImageFormat = apps.get_model('package', 'ImageFormat')
    for format in formats:
        ImageFormat.objects.create(name=format)


def create_image_types(apps, schema_editor):
    types = [
        'boot',
        'cd',
        'dvd',
        'ec2',
        'kvm',
        'live',
        'netinst',
        'p2v',
        'rescue',
    ]
    ImageType = apps.get_model('package', 'ImageType')
    for type in types:
        ImageType.objects.create(name=type)


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_image_types),
        migrations.RunPython(create_image_formats),
    ]
