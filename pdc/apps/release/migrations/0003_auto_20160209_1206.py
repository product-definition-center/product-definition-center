# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0002_auto_20150512_0719'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ('short',)},
        ),
        migrations.AlterModelOptions(
            name='productversion',
            options={'ordering': ('product_version_id',)},
        ),
    ]
