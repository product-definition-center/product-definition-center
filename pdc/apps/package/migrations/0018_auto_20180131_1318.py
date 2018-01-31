# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0017_auto_20171103_0645'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rpm',
            options={'ordering': ('name', 'epoch', 'version', 'release', 'arch')},
        ),
    ]
