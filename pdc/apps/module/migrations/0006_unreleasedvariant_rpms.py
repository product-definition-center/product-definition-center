# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0013_set_default_subvariant_to_empty_string'),
        ('tree', '0005_unreleasedvariant_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='unreleasedvariant',
            name='rpms',
            field=models.ManyToManyField(to='package.RPM'),
        ),
    ]
