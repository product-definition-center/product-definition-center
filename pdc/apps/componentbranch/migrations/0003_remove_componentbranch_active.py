# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('componentbranch', '0002_componentbranch_critical_path'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='componentbranch',
            name='active',
        ),
    ]
