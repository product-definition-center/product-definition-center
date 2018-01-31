# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compose', '0012_auto_20160615_0611'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='composeimage',
            options={'ordering': ('variant_arch', 'image')},
        ),
        migrations.AlterModelOptions(
            name='composetree',
            options={'ordering': ('compose', 'variant', 'arch', 'location', 'scheme')},
        ),
    ]
