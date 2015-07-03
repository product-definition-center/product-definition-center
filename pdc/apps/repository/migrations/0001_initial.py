# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ContentFormat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Repo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shadow', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=2000, db_index=True)),
                ('product_id', models.PositiveIntegerField(null=True, blank=True)),
                ('content_category', models.ForeignKey(to='repository.ContentCategory')),
                ('content_format', models.ForeignKey(to='repository.ContentFormat')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='RepoFamily',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('description', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='repo',
            name='repo_family',
            field=models.ForeignKey(to='repository.RepoFamily'),
        ),
        migrations.AddField(
            model_name='repo',
            name='service',
            field=models.ForeignKey(to='repository.Service'),
        ),
        migrations.AddField(
            model_name='repo',
            name='variant_arch',
            field=models.ForeignKey(related_name='repos', on_delete=django.db.models.deletion.PROTECT, to='release.VariantArch'),
        ),
        migrations.AlterUniqueTogether(
            name='repo',
            unique_together=set([('variant_arch', 'service', 'repo_family', 'content_format', 'content_category', 'name', 'shadow')]),
        ),
    ]
