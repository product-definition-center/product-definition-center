#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import django
from django.apps import apps
import subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'pdc.settings_graph_models'

file_contents = '''.. _model_graphs:


PDC Model Graphs
================

Current PDC Model Graphs:
'''


SECTION = '''
{0}
{1}

.. image:: models_svg/{0}.svg
'''


def run_cmd(args):
    print(' '.join(args))
    res = subprocess.call(args)
    if res != 0:
        print('Failed')
        sys.exit(1)


django.setup()

run_cmd(['python', 'manage.py', 'graph_models', '-aE',
         '-o', 'docs/source/models_svg/overview.svg'])
file_contents += SECTION.format('overview', '-' * len('overview'))

for config in sorted(apps.get_app_configs(), key=lambda x: x.label):
    if not config.name.startswith('pdc.') or config.models_module is None:
        continue

    try:
        label = config.label
    except ValueError:
        sys.exit(1)

    run_cmd(['python', 'manage.py', 'graph_models', '-gE', label,
             '-o', 'docs/source/models_svg/{}.svg'.format(label)])
    file_contents += SECTION.format(label, '-' * len(label))

with open('docs/source/model_graphs.rst', 'w') as f:
    f.write(file_contents)
