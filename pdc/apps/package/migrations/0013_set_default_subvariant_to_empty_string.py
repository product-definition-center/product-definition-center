# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def set_default_subvariant(apps, schema_editor):
    for image in apps.get_model('package', 'Image').objects.filter(subvariant=None):
        image.subvariant = ""
        image.save()

def reverse_subvariant(apps, schema_editor):
    for image in apps.get_model('package', 'Image').objects.filter(subvariant=''):
        image.subvariant = None
        image.save()


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0012_image_payload'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='subvariant',
            field=models.CharField(default=b'', max_length=4096, blank=True),
        ),
        migrations.RunPython(set_default_subvariant, reverse_code=reverse_subvariant),
    ]

