# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0002_auto_20150512_0719'),
    ]

    operations = [
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('short', models.CharField(unique=True, max_length=100)),
                ('name', models.CharField(max_length=250)),
                ('binary', models.BooleanField(default=True)),
                ('source', models.BooleanField(default=True)),
                ('enabled', models.BooleanField(default=True)),
                ('ftp_dir', models.CharField(max_length=500)),
                ('rsync_dir', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='PartnerMapping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('partner', models.ForeignKey(to='partners.Partner')),
                ('variant_arch', models.ForeignKey(to='release.VariantArch')),
            ],
        ),
        migrations.CreateModel(
            name='PartnerType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='partner',
            name='type',
            field=models.ForeignKey(to='partners.PartnerType'),
        ),
        migrations.AlterUniqueTogether(
            name='partnermapping',
            unique_together=set([('partner', 'variant_arch')]),
        ),
    ]
