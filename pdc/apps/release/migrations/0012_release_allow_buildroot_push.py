# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0011_auto_20170912_1108'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='allow_buildroot_push',
            field=models.BooleanField(default=False),
        ),
    ]
