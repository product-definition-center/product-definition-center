# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0014_auto_20170922_0804'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variantcpe',
            name='cpe',
            field=models.ForeignKey(to='release.CPE', on_delete=django.db.models.deletion.PROTECT),
        ),
    ]
