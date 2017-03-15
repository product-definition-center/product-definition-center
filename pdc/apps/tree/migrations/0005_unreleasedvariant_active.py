# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tree', '0004_modulemd'),
    ]

    operations = [
        migrations.AddField(
            model_name='unreleasedvariant',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
