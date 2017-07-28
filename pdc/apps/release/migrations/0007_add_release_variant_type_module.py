# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


def create_variant_type_module(apps, schema_editor):
    VariantType = apps.get_model('release', 'VariantType')
    VariantType.objects.create(name='module')


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0006_auto_20160512_0515'),
    ]

    operations = [
        migrations.RunPython(create_variant_type_module),
    ]
