# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tree', '0002_builddependency_runtimedependency'),
    ]

    operations = [
        migrations.AddField(
            model_name='builddependency',
            name='stream',
            field=models.CharField(default='master', max_length=300),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='runtimedependency',
            name='stream',
            field=models.CharField(default='master', max_length=300),
            preserve_default=False,
        ),
    ]
