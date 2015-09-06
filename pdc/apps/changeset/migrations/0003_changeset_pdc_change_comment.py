# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0002_auto_20150525_1410'),
    ]

    operations = [
        migrations.AddField(
            model_name='changeset',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
    ]
