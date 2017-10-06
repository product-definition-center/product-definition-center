# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('component', '0012_auto_20160928_1838'),
        ('contact', '0006_auto_20151127_0837'),
        ('repository', '0003_pushtarget'),
    ]

    operations = [
        migrations.CreateModel(
            name='MultiDestination',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True)),
                ('destination_repo', models.ForeignKey(related_name='destination_repo', to='repository.Repo')),
                ('global_component', models.ForeignKey(to='component.GlobalComponent')),
                ('origin_repo', models.ForeignKey(related_name='origin_repo', to='repository.Repo')),
                ('subscribers', models.ManyToManyField(to='contact.Person', blank=True)),
            ],
            options={
                'ordering': ['global_component'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='multidestination',
            unique_together=set([('global_component', 'origin_repo', 'destination_repo')]),
        ),
    ]
