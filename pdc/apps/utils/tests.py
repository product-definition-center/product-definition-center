#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from datetime import datetime
import random
import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from .templatetags.epochformat import epochformat


class EpochFormatTest(TestCase):

    def test_for_selected_values(self):
        data = [
            (1412695330, "2014-10-07 15:22:10"),
            (datetime(2014, 10, 7, 15, 22, 10), "2014-10-07 15:22:10"),
            (1388534400, "2014-01-01 00:00:00"),
            (datetime(2014, 1, 1), "2014-01-01 00:00:00"),
        ]
        for ts, expected in data:
            self.assertEqual(expected, epochformat(ts))

    def test_random_values(self):
        """Generate random timestamps, check that parsing after formatting gives same time."""
        for _ in range(100):
            ts = random.randint(1, 2 ** 32 - 1)
            returned = datetime.strptime(epochformat(ts), "%Y-%m-%d %H:%M:%S") - datetime(1970, 1, 1)
            # In Python 2.7 there is a method for this. Jenkins however uses Python 2.6.
            total_seconds = returned.seconds + returned.days * 24 * 3600
            self.assertEqual(ts, total_seconds)


class APIRootTestCase(APITestCase):
    def test_api_root_is_sorted(self):
        rsp = self.client.get(reverse('api-root'))
        self.assertEqual(rsp.status_code, status.HTTP_200_OK)
        self.assertEqual(rsp.data.keys(), sorted(rsp.data.keys()))

    def test_root_includes_release_component_contacts(self):
        response = self.client.get(reverse('api-root'))
        self.assertIn('release-component-contacts', response.data)

    def test_root_includes_release_rpm_mapping(self):
        response = self.client.get(reverse('api-root'))
        key = 'releases/{release_id}/rpm-mapping'
        self.assertIn(key, response.data)
        self.assertEqual(response.data[key],
                         'http://testserver/rest_api/v1/releases/{release_id}/rpm-mapping/{package}/')


class TestCacheRESTTestCase(APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
    ]

    def test_cache(self):
        tmp = settings.CACHE_MIDDLEWARE_SECONDS
        settings.CACHE_MIDDLEWARE_SECONDS = 10

        response = self.client.get(reverse('baseproduct-list'))
        self.assertEqual(response.data['count'], 0)

        args = {"name": "Our Awesome Product", "short": "product", "version": "1", "release_type": "ga"}
        response = self.client.post(reverse('baseproduct-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(reverse('baseproduct-list'))
        self.assertEqual(response.data['count'], 0)
        self.assertTrue(response.has_header('Cache-Control'))
        self.assertTrue(response.has_header('Last-Modified'))

        time.sleep(11)
        response = self.client.get(reverse('baseproduct-list'))
        self.assertEqual(response.data['count'], 1)

        settings.CACHE_MIDDLEWARE_SECONDS = tmp
