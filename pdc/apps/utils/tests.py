#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from datetime import datetime
import random
import time

from django.conf import settings
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from .templatetags.epochformat import epochformat

from .rpm import parse_nvr, parse_nvra


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


class TestRpmParseNvr(TestCase):
    def test_valid_nvr(self):
        self.assertEqual(parse_nvr("net-snmp-5.3.2.2-5.el5"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch=""))
        self.assertEqual(parse_nvr("1:net-snmp-5.3.2.2-5.el5"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("net-snmp-1:5.3.2.2-5.el5"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("net-snmp-5.3.2.2-5.el5:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("/net-snmp-5.3.2.2-5.el5:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("/1:net-snmp-5.3.2.2-5.el5"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("foo/net-snmp-5.3.2.2-5.el5:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("foo/1:net-snmp-5.3.2.2-5.el5"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("/foo/bar/net-snmp-5.3.2.2-5.el5:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))
        self.assertEqual(parse_nvr("/foo/bar/1:net-snmp-5.3.2.2-5.el5"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1"))

        # test for name which contains the version number and a dash
        self.assertEqual(parse_nvr("openmpi-1.10-1.10.2-2.el6"), dict(name="openmpi-1.10", version="1.10.2", release="2.el6", epoch=""))

    def test_invalid_nvr(self):
        self.assertRaises(ValueError, parse_nvr, "net-snmp")
        self.assertRaises(ValueError, parse_nvr, "net-snmp-5.3.2.2-1:5.el5")
        self.assertRaises(ValueError, parse_nvr, "1:net-snmp-5.3.2.2-5.el5:1")
        self.assertRaises(ValueError, parse_nvr, "1:net-snmp-1:5.3.2.2-5.el5")
        self.assertRaises(ValueError, parse_nvr, "net-snmp-1:5.3.2.2-5.el5:1")
        self.assertRaises(ValueError, parse_nvr, "1:net-snmp-1:5.3.2.2-5.el5:1")


class TestRpmParseNvra(TestCase):
    def test_valid_nvra(self):
        self.assertEqual(parse_nvra("net-snmp-5.3.2.2-5.el5.i386"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="", arch="i386", src=False))
        self.assertEqual(parse_nvra("net-snmp-5.3.2.2-5.el5.i386.rpm"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="", arch="i386", src=False))
        self.assertEqual(parse_nvra("net-snmp-5.3.2.2-5.el5.src.rpm"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="", arch="src", src=True))

        self.assertEqual(parse_nvra("/net-snmp-5.3.2.2-5.el5.src.rpm:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="src", src=True))
        self.assertEqual(parse_nvra("/1:net-snmp-5.3.2.2-5.el5.src.rpm"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="src", src=True))
        self.assertEqual(parse_nvra("foo/net-snmp-5.3.2.2-5.el5.src.rpm:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="src", src=True))
        self.assertEqual(parse_nvra("foo/1:net-snmp-5.3.2.2-5.el5.src.rpm"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="src", src=True))
        self.assertEqual(parse_nvra("/foo/bar/net-snmp-5.3.2.2-5.el5.src.rpm:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="src", src=True))
        self.assertEqual(parse_nvra("/foo/bar/1:net-snmp-5.3.2.2-5.el5.src.rpm"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="src", src=True))

        self.assertEqual(parse_nvra("/foo/bar/net-snmp-devel-5.7.3-27.el8+5.x86_64.rpm"), dict(name="net-snmp-devel", version="5.7.3", release="27.el8+5", epoch="", arch="x86_64", src=False))
        self.assertEqual(parse_nvra("/foo/bar/net-snmp-devel-2:5.7.3-27.el8+5.x86_64.rpm"), dict(name="net-snmp-devel", version="5.7.3", release="27.el8+5", epoch="2", arch="x86_64", src=False))

        self.assertEqual(parse_nvra("net-snmp-devel-5.7.3-27.el8+5.x86_64:2"), dict(name="net-snmp-devel", version="5.7.3", release="27.el8+5", epoch="2", arch="x86_64", src=False))
        self.assertEqual(parse_nvra("net-snmp-devel-2:5.7.3-27.el8+5.x86_64"), dict(name="net-snmp-devel", version="5.7.3", release="27.el8+5", epoch="2", arch="x86_64", src=False))
        self.assertEqual(parse_nvra("2:net-snmp-devel-5.7.3-27.el8+5.x86_64"), dict(name="net-snmp-devel", version="5.7.3", release="27.el8+5", epoch="2", arch="x86_64", src=False))
        self.assertEqual(parse_nvra("net-snmp-devel-5.7.3-27.el8+5:2.x86_64"), dict(name="net-snmp-devel", version="5.7.3", release="27.el8+5", epoch="2", arch="x86_64", src=False))
        self.assertEqual(parse_nvra("net-snmp-devel-5.7.3-27.el8+5:2.x86_64.rpm"), dict(name="net-snmp-devel", version="5.7.3", release="27.el8+5", epoch="2", arch="x86_64", src=False))

    def test_invalid_nvra(self):
        self.assertEqual(parse_nvra("net-snmp-5.3.2.2-5.el5.i386.rpm:1"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="i386", src=False))
        self.assertEqual(parse_nvra("net-snmp-5.3.2.2-5.el5.i386:1.rpm"), dict(name="net-snmp", version="5.3.2.2", release="5.el5", epoch="1", arch="i386", src=False))
        self.assertRaises(ValueError, parse_nvra, "net-snmp-5.3.2.2-5")


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
