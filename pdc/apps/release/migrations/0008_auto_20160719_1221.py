# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0007_add_release_variant_type_module'),
    ]

    operations = [
        migrations.AddField(
            model_name='variant',
            name='variant_release',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='variant',
            name='variant_version',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
