#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_empty_path(apps, schema_editor):
    path, _ = apps.get_model('compose', 'Path').objects.get_or_create(path='')
    for compose_image in apps.get_model('compose', 'ComposeImage').objects.filter(path=None):
        compose_image.path = path
        compose_image.save()


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0004_auto_20150819_0826'),
    ]

    operations = [
        migrations.RunPython(set_empty_path),
        migrations.AlterField(
            model_name='composeimage',
            name='path',
            field=models.ForeignKey(to='compose.Path'),
        ),
    ]
