# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0015_auto_20171101_0609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='releasedfiles',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
