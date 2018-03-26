#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# https://opensource.org/licenses/MIT
#

import unittest

from .serializers import _normalized_fields_set


class TestNormalizedFieldsSet(unittest.TestCase):
    def test_normal(self):
        self.assertEqual(_normalized_fields_set("a"), set(['a']))
        self.assertEqual(_normalized_fields_set(["a"]), set(['a']))
        self.assertEqual(_normalized_fields_set(["a", "b"]), set(['a', 'b']))

    def test_empty(self):
        self.assertEqual(_normalized_fields_set(None), set())
        self.assertEqual(_normalized_fields_set([]), set())
        self.assertEqual(_normalized_fields_set(['']), set())

    def test_comma_separated(self):
        self.assertEqual(_normalized_fields_set("a,b"), set(['a', 'b']))
        self.assertEqual(_normalized_fields_set(["a,b"]), set(['a', 'b']))
        self.assertEqual(_normalized_fields_set(["a,b", "c"]), set(['a', 'b', 'c']))

    def test_trailing_comma(self):
        self.assertEqual(_normalized_fields_set(','), set())
        self.assertEqual(_normalized_fields_set('a,'), set(['a']))
