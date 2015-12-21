# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0006_auto_20151030_0845'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buildimage',
            name='image_id',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterUniqueTogether(
            name='buildimage',
            unique_together=set([('image_id', 'image_format')]),
        ),
    ]
