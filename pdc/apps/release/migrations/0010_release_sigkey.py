# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0002_auto_20150512_0703'),
        ('release', '0009_variantcpe'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='sigkey',
            field=models.ForeignKey(blank=True, to='common.SigKey', null=True),
        ),
    ]
