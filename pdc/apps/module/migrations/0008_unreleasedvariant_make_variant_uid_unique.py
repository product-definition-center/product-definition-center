# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('module', '0007_unreleasedvariant_context_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unreleasedvariant',
            name='variant_uid',
            field=models.CharField(unique=True, max_length=200),
        )
    ]
