# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_new_image_type_and_format(apps, schema_editor):
    formats = [
        'tar.gz',
        'tar.xz'
    ]
    ImageFormat = apps.get_model('package', 'ImageFormat')
    for format in formats:
        ImageFormat.objects.get_or_create(name=format)

    ImageType = apps.get_model('package', 'ImageType')
    ImageType.objects.get_or_create(name='docker')


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0010_auto_20160218_1339'),
    ]

    operations = [
        migrations.RunPython(add_new_image_type_and_format)
    ]
