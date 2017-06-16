# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tree', '0003_dep_stream'),
    ]

    operations = [
        migrations.AddField(
            model_name='UnreleasedVariant',
            name='modulemd',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
