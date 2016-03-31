# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from productmd.common import create_release_id


def set_baseproduct_id(obj):
    obj.base_product_id = create_release_id(obj.short.lower(), obj.version, obj.release_type.short)


def set_release_id(obj):
    bp_dict = {}
    if obj.base_product:
        bp_dict = {
            "bp_short": obj.base_product.short.lower(),
            "bp_version": obj.base_product.version,
            "bp_type": obj.base_product.release_type.short,
        }
    obj.release_id = create_release_id(obj.short.lower(), obj.version, obj.release_type.short, **bp_dict)


def populate_baseproduct_release_type(apps, schema_editor):
    release_type_model = apps.get_model('release', 'BaseProduct')
    try:
        release_type = release_type_model.objects.get(name="ga")
    except release_type_model.DoesNotExist:
        return
    model = apps.get_model('release', 'BaseProduct')
    for i in model.objects.all():
        i.type = release_type
        # re-generate base_product_id to the new format
        set_base_product_id(i)
        i.save()


def create_new_release_id(apps, schema_editor):
    model = apps.get_model('release', 'Release')
    for i in model.objects.all():
        # re-generate release_id to the new format
        set_release_id(i)
        i.save()


class Migration(migrations.Migration):

    dependencies = [
        ('release', '0004_auto_20160308_1614'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseproduct',
            name='release_type',
            field=models.ForeignKey(default=1, to='release.ReleaseType'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='baseproduct',
            unique_together=set([('name', 'version', 'release_type'), ('short', 'version', 'release_type')]),
        ),
        migrations.RunPython(populate_baseproduct_release_type),
        migrations.RunPython(create_new_release_id),
    ]
