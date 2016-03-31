# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0003_auto_20160209_1206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseproduct',
            name='short',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]+([a-z0-9]*-?[a-z0-9]+)*$', message=b'Only accept lowercase letters, numbers or -')]),
        ),
        migrations.AlterField(
            model_name='product',
            name='short',
            field=models.CharField(unique=True, max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]+([a-z0-9]*-?[a-z0-9]+)*$', message=b'Only accept lowercase letters, numbers or -')]),
        ),
        migrations.AlterField(
            model_name='productversion',
            name='short',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]+([a-z0-9]*-?[a-z0-9]+)*$', message=b'Only accept lowercase letters, numbers or -')]),
        ),
        migrations.AlterField(
            model_name='productversion',
            name='version',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^([^0-9].*|([0-9]+(\\.?[0-9]+)*))$', message=b'Only accept comma separated numbers or any text')]),
        ),
        migrations.AlterField(
            model_name='release',
            name='short',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^[a-z]+([a-z0-9]*-?[a-z0-9]+)*$', message=b'Only accept lowercase letters, numbers or -')]),
        ),
        migrations.AlterField(
            model_name='release',
            name='version',
            field=models.CharField(max_length=200, validators=[django.core.validators.RegexValidator(regex=b'^([^0-9].*|([0-9]+(\\.?[0-9]+)*))$', message=b'Only accept comma separated numbers or any text')]),
        ),
    ]
