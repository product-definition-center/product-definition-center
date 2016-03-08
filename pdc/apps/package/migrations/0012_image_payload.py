# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0011_auto_20160219_0915'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='subvariant',
            field=models.CharField(max_length=4096, null=True, blank=True),
        ),
    ]
