# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import unicode_literals

from django.db import models, migrations


def create_arches(apps, schema_editor):
    # When adding new architectures to this list, make sure to add them at the
    # end. There are tests referencing architectures through their database pk.
    arches = [
        "alpha",
        "alphaev4",
        "alphaev45",
        "alphaev5",
        "alphaev56",
        "alphaev6",
        "alphaev67",
        "alphaev68",
        "alphaev7",
        "alphapca56",
        "amd64",
        "arm64",
        "armv5tejl",
        "armv5tel",
        "armv6l",
        "armv7hl",
        "armv7hnl",
        "armv7l",
        "athlon",
        "geode",
        "i386",
        "i486",
        "i586",
        "i686",
        "ia32e",
        "ia64",
        "noarch",
        "nosrc",
        "ppc",
        "ppc64",
        "ppc64iseries",
        "ppc64le",
        "ppc64p7",
        "ppc64pseries",
        "s390",
        "s390x",
        "sh3",
        "sh4",
        "sh4a",
        "sparc",
        "sparc64",
        "sparc64v",
        "sparcv8",
        "sparcv9",
        "sparcv9v",
        "src",
        "x86_64",
        "aarch64",
    ]
    Arch = apps.get_model('common', 'Arch')
    for arch in arches:
        Arch.objects.create(name=arch)


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_arches),
    ]
