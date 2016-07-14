# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0006_auto_20150914_0308'),
    ]

    operations = [
        migrations.AlterField(
            model_name='change',
            name='target_class',
            field=models.CharField(max_length=200, db_index=True),
        ),
    ]
