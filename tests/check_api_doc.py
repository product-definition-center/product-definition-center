#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
"""
Checks for automatic documentation generators. It verifies no errors are
logged.

This test should not be part of main test suite as it will run pretty much all
viewsets without checking anything but the documentation. This makes the code
coverage go up significantly while there are in fact no tests about those parts
of code.
"""
import mock

from django.urls import reverse
from rest_framework.test import APITestCase


class AutoDocTestCase(APITestCase):
    def test_no_page_logs_error(self):
        root = self.client.get(reverse('api-root'))
        for _, url in root.data.iteritems():
            with mock.patch('logging.getLogger') as getLogger:
                self.client.get(url, HTTP_ACCEPT='text/html')
                err = getLogger.return_value.error
                self.assertFalse(err.called,
                                 "%s has bad documentation\nError: %s" % (url, err.call_args))
