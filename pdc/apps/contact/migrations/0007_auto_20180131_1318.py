# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0006_auto_20151127_0837'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='globalcomponentcontact',
            options={'ordering': ('role', 'component', 'contact')},
        ),
        migrations.AlterModelOptions(
            name='releasecomponentcontact',
            options={'ordering': ('role', 'component', 'contact')},
        ),
    ]
