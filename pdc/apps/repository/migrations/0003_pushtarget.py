# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0002_auto_20150512_0724'),
    ]

    operations = [
        migrations.CreateModel(
            name='PushTarget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, db_index=True)),
                ('description', models.CharField(max_length=300, blank=True)),
                ('host', models.URLField(max_length=255, blank=True)),
                ('service', models.ForeignKey(to='repository.Service')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
