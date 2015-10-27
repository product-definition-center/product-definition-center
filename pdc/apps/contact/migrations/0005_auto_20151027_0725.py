# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0004_auto_20151016_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactrole',
            name='count_limit',
            field=models.PositiveSmallIntegerField(default=1, help_text='Contact count limit of the role for each component.'),
        ),
    ]
