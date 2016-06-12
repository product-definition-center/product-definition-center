# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0005_auto_20160314_1532'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('description', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('releases', models.ManyToManyField(to='release.Release', blank=True)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='ReleaseGroupType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='releasegroup',
            name='type',
            field=models.ForeignKey(to='release.ReleaseGroupType'),
        ),
    ]
