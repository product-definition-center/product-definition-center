# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0016_auto_20180131_0312'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cpe',
            options={'ordering': ('cpe',)},
        ),
        migrations.AlterModelOptions(
            name='releasetype',
            options={'ordering': ('short', 'name', 'suffix')},
        ),
        migrations.AlterModelOptions(
            name='variantcpe',
            options={'ordering': ('variant', 'cpe')},
        ),
    ]
