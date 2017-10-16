# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0010_release_sigkey'),
    ]

    operations = [
        migrations.CreateModel(
            name='CPE',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cpe', models.CharField(unique=True, max_length=300)),
                ('description', models.CharField(max_length=300, blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='variantcpe',
            name='cpe',
        ),
        migrations.AddField(
            model_name='variantcpe',
            name='cpe',
            field=models.ForeignKey(to='release.CPE'),
        ),
    ]
