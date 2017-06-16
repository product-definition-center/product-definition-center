# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('module', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuildDependency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dependency', models.CharField(max_length=300)),
                ('variant', models.ForeignKey(related_name='build_deps', to='module.UnreleasedVariant')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RuntimeDependency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dependency', models.CharField(max_length=300)),
                ('variant', models.ForeignKey(related_name='runtime_deps', to='module.UnreleasedVariant')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
