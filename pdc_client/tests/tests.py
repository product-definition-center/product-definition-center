# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import unittest

from .. import plugin_helpers


class PluginHelperTestCase(unittest.TestCase):
    def test_extract_arguments(self):
        class Temp(object):
            pass
        args = Temp()
        setattr(args, 'prf__foo__bar__baz', 1)
        setattr(args, 'prf__foo__bar__quux', 2)
        data = plugin_helpers.extract_arguments(args, prefix='prf__')
        self.assertDictEqual(data,
                             {'foo': {'bar': {'baz': 1, 'quux': 2}}})
