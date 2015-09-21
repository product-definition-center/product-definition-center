# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


import argparse
import errno
import logging
import os


PLUGIN_TEMPLATE = '''
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from pdc_client import plugin_helpers


class {class_name}(plugin_helpers.PDCClientPlugin):
    def register(self):
        pass


PLUGIN_CLASSES = [{class_name}]
'''


TEST_TEMPLATE = '''
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc_client.test_helpers import CLITestCase
from pdc_client.runner import Runner


class {name}TestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()
'''


def write_file(name, contents):
    try:
        with open(name, 'wx') as f:
            f.write(contents)
    except IOError as err:
        if err.errno == errno.EEXIST:
            logging.warning('Not overwriting %s', name)
        else:
            logging.error('Unhandled exception', exc_info=err)
    else:
        logging.info('Created %s (%d bytes)', name, len(contents))


def create_plugin(name):
    filepath = os.path.join('pdc_client', 'plugins', name + '.py')
    class_name = '{}Plugin'.format(name.capitalize())
    data = PLUGIN_TEMPLATE.format(class_name=class_name).lstrip()
    write_file(filepath, data)


def create_tests(name):
    path = os.path.join('pdc_client', 'tests', name)
    try:
        os.makedirs(os.path.join(path, 'data'))
        logging.info('Created %s/', os.path.join(path, 'data'))
    except os.error:
        pass
    write_file(os.path.join(path, '__init__.py'), '')
    data = TEST_TEMPLATE.format(name=name.capitalize()).lstrip()
    write_file(os.path.join(path, 'tests.py'), data)


def main():
    parser = argparse.ArgumentParser('create-plugin.py')
    parser.add_argument('name', metavar='NAME')
    parser.add_argument('--skip-tests', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    options = parser.parse_args()
    logging.basicConfig(level=logging.INFO if options.verbose else logging.WARNING,
                        format='%(levelname)s: %(message)s')
    name = options.name
    create_plugin(name)
    if not options.skip_tests:
        create_tests(name)


if __name__ == '__main__':
    main()
