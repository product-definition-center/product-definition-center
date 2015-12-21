# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0005_auto_20151027_0725'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='rolecontact',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='rolecontact',
            name='contact',
        ),
        migrations.RemoveField(
            model_name='rolecontact',
            name='contact_role',
        ),
        migrations.DeleteModel(
            name='RoleContact',
        ),
    ]
