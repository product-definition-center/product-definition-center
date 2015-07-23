# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0002_auto_20150512_0719'),
        ('package', '0002_auto_20150512_0714'),
    ]

    operations = [
        migrations.AddField(
            model_name='buildimage',
            name='releases',
            field=models.ManyToManyField(to='release.Release'),
        ),
    ]
