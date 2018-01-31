# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0015_auto_20171004_0807'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variantcpe',
            name='variant',
            field=models.ForeignKey(to='release.Variant'),
        ),
    ]
