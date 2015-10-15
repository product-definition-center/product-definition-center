# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0003_auto_20151001_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='contactrole',
            name='count_limit',
            field=models.IntegerField(default=1, help_text='Contact count limit of the role for each component.'),
        ),
        migrations.AlterUniqueTogether(
            name='globalcomponentcontact',
            unique_together=set([('role', 'component', 'contact')]),
        ),
        migrations.AlterUniqueTogether(
            name='releasecomponentcontact',
            unique_together=set([('role', 'component', 'contact')]),
        ),
    ]
