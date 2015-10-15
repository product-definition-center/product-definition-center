# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('partners', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='partner',
            name='ftp_dir',
            field=models.CharField(max_length=500, blank=True),
        ),
        migrations.AlterField(
            model_name='partner',
            name='rsync_dir',
            field=models.CharField(max_length=500, blank=True),
        ),
    ]
