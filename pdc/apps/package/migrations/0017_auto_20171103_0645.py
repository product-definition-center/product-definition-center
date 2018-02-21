# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0016_auto_20171101_0736'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='releasedfiles',
            name='build',
        ),
        migrations.RemoveField(
            model_name='releasedfiles',
            name='file',
        ),
        migrations.RemoveField(
            model_name='releasedfiles',
            name='package',
        ),
    ]
