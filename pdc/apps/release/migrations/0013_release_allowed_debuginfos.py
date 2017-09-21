# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0002_auto_20150512_0724'),
        ('release', '0012_release_allow_buildroot_push'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='allowed_debuginfo_services',
            field=models.ManyToManyField(to='repository.Service', blank=True),
        ),
    ]
