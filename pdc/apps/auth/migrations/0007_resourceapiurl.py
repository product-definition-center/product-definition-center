# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kerb_auth', '0006_auto_20160519_0901'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResourceApiUrl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=255, blank=True)),
                ('resource', models.OneToOneField(related_name='api_url', to='kerb_auth.Resource')),
            ],
            options={
                'ordering': ('resource__name',),
            },
        ),
    ]
