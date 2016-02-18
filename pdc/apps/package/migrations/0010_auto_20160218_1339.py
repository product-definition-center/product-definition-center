# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0009_rpm_built_for_release'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='implant_md5',
            field=models.CharField(max_length=32, null=True, blank=True),
        ),
    ]
