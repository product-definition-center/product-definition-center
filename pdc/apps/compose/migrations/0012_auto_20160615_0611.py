# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0011_remove_duplicate_pathtypes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pathtype',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]
