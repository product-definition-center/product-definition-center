# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations

def set_default_type(apps, schema_editor):
    type = apps.get_model('component', 'ReleaseComponentType').objects.get(name='rpm')
    for component in apps.get_model('component', 'ReleaseComponent').objects.filter(type=None):
        component.type = type
        component.save()


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0005_auto_20150727_0929'),
    ]

    operations = [
        migrations.RunPython(set_default_type),
    ]
