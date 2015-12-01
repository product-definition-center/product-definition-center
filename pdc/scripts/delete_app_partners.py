#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import django
import os


if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'pdc.settings'
    django.setup()

    from django.contrib.contenttypes.models import ContentType
    from django.db import connection
    from django.db.utils import OperationalError

    for c in ContentType.objects.all().order_by("app_label", "model"):
        if not c.model_class():
            print('Deleting Content Type %s %s' % (c.app_label, c.model))
            c.delete()

    tables = ['partners_partner', 'partners_partnermapping', 'partners_partnertype']

    cursor = connection.cursor()
    for t in tables:
        try:
            cursor.execute("DROP TABLE %s" % t)
        except OperationalError:
            pass
