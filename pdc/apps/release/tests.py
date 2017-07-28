# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import time

from rest_framework.test import APITestCase
from rest_framework import status
from django.core.urlresolvers import reverse
from django.test.client import Client

from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin
from . import models
from pdc.apps.bindings.models import ReleaseBugzillaMapping, ReleaseDistGitMapping
from pdc.apps.compose import models as compose_models


class BaseProductRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
    ]

    def test_create(self):
        args = {"name": "Our Awesome Product", "short": "product", "version": "1", "release_type": "ga"}
        response = self.client.post(reverse('baseproduct-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({'base_product_id': 'product-1'})
        self.assertEqual(args, dict(response.data))
        self.assertEqual(1, len(models.BaseProduct.objects.filter(base_product_id='product-1')))
        self.assertNumChanges([1])

    def test_create_with_invalid_short(self):
        args = {"name": "Fedora", "short": "F", "version": "1", "release_type": "ga"}
        response = self.client.post(reverse('baseproduct-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('Only accept lowercase letters, numbers or -', response.data['short'])

    def test_create_with_extra_fields(self):
        args = {"name": "Fedora", "short": "f", "version": "1", "release_type": "ga", "foo": "bar"}
        response = self.client.post(reverse('baseproduct-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')

    def test_create_duplicate(self):
        args = {"name": "Our Awesome Product", "short": "product", "version": "1", "release_type": "ga"}
        response = self.client.post(reverse('baseproduct-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.post(reverse('baseproduct-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_put_as_create_disabled(self):
        args = {"name": "Our Awesome Product", "short": "product", "version": "1", "release_type": "ga"}
        response = self.client.put(reverse('baseproduct-detail', args=['product']), args)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([])

    def test_update(self):
        self.test_create()
        response = self.client.put(reverse('baseproduct-detail', args=['product-1']),
                                   {'short': 'product', 'name': 'OUR AWESOME PRODUCT',
                                    'version': '1', 'release_type': 'ga'},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.BaseProduct.objects.get(base_product_id='product-1').name,
                         'OUR AWESOME PRODUCT')
        self.assertNumChanges([1, 1])

    def test_update_missing_field(self):
        self.test_create()
        response = self.client.put(reverse('baseproduct-detail', args=['product-1']),
                                   {'short': 'product'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([1])

    def test_update_partial(self):
        self.test_create()
        response = self.client.patch(reverse('baseproduct-detail', args=['product-1']),
                                     {'name': 'Our Product'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1, 1])
        self.assertEqual(models.BaseProduct.objects.get(base_product_id='product-1').name,
                         'Our Product')

    def test_update_only_short(self):
        self.test_create()
        response = self.client.patch(reverse('baseproduct-detail', args=['product-1']),
                                     {'short': 'tcudorp'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1, 1])
        response = self.client.get(reverse('baseproduct-detail', args=['product-1']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('baseproduct-detail', args=['tcudorp-1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_only_version(self):
        self.test_create()
        response = self.client.patch(reverse('baseproduct-detail', args=['product-1']),
                                     {'version': '2'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1, 1])
        response = self.client.get(reverse('baseproduct-detail', args=['product-1']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('baseproduct-detail', args=['product-2']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_query_with_multi_values(self):
        args = {"name": "Our Awesome Product1", "short": "product", "version": "1", "release_type": "ga"}
        self.client.post(reverse('baseproduct-list'), args)
        args = {"name": "Our Awesome Product2", "short": "product", "version": "2", "release_type": "ga"}
        self.client.post(reverse('baseproduct-list'), args)
        url = reverse('baseproduct-list')
        response = self.client.get(url + '?version=1&version=2')
        self.assertEqual(2, response.data['count'])


class ProductRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/product.json",
    ]

    def test_create(self):
        args = {"name": "Fedora", "short": "f"}
        response = self.client.post(reverse('product-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({'active': False, 'product_versions': []})
        self.assertEqual(args, response.data)
        self.assertNumChanges([1])

    def test_create_invalid_short(self):
        args = {'name': 'Fedora', 'short': 'F'}
        response = self.client.post(reverse('product-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('Only accept lowercase letters, numbers or -', response.data['short'])

    def test_create_with_extra_field(self):
        args = {'name': 'Fedora', 'short': 'f', 'foo': 'bar'}
        response = self.client.post(reverse('product-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')

    def test_create_duplicate(self):
        args = {"name": "Fedora", "short": "f"}
        response = self.client.post(reverse('product-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        response = self.client.post(reverse('product-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_create_with_bad_field(self):
        args = {"name": "Fedora", "short": "f", "foo": "bar"}
        response = self.client.post(reverse('product-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get(self):
        response = self.client.get(reverse('product-detail', args=['product']))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(dict(response.data),
                         {"short": "product", "name": "Test Product",
                          "product_versions": [], "active": False})

    def test_all(self):
        response = self.client.get(reverse('product-list'))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(2, response.data['count'])
        data = response.data['results']
        expected = [
            {'name': u'Dummy product',
             'short': u'dummy',
             'active': False,
             'product_versions': []},
            {'name': u'Test Product',
             'short': u'product',
             'active': False,
             'product_versions': []},
        ]
        self.assertEqual(sorted(data), sorted(expected))

    def test_get_after_create(self):
        self.test_create()
        response = self.client.get(reverse('product-detail', args=["f"]))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.data, {"short": "f",
                                         "name": "Fedora",
                                         "active": False,
                                         "product_versions": []})

    def test_query_with_illegal_active(self):
        response = self.client.get(reverse('product-list'), {"active": "abcd"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_multi_values(self):
        response = self.client.get(reverse('product-list') + '?short=product&short=dummy')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)


class ProductUpdateTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/product.json",
    ]

    def test_update(self):
        response = self.client.put(reverse('product-detail', args=['product']),
                                   {'short': 'product', 'name': 'MY PRODUCT'},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.Product.objects.get(short='product').name, 'MY PRODUCT')
        self.assertNumChanges([1])

    def test_put_as_create_disabled(self):
        args = {"name": "Product", "short": "p"}
        response = self.client.put(reverse('product-detail', args=['p']), args)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([])

    def test_update_missing_field(self):
        response = self.client.put(reverse('product-detail', args=['product']),
                                   {'short': 'product'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_partial(self):
        response = self.client.patch(reverse('product-detail', args=['product']),
                                     {'name': 'tcudorp'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(models.Product.objects.get(short='product').name, 'tcudorp')

    def test_partial_update_empty(self):
        url = reverse('product-detail', args=['product'])
        response = self.client.patch(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_only_short(self):
        response = self.client.patch(reverse('product-detail', args=['product']),
                                     {'short': 'tcudorp'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        response = self.client.get(reverse('product-detail', args=['product']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('product-detail', args=['tcudorp']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_read_only_field(self):
        response = self.client.patch(reverse('product-detail', args=['product']),
                                     {'active': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])


class ProductVersionRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/release/fixtures/tests/product_version.json",
    ]

    def test_create(self):
        args = {"name": "Our Awesome Product", "short": "product",
                "version": "2", "product": "product"}
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({'product_version_id': 'product-2',
                     'active': False,
                     'releases': [],
                     'product': 'product'})
        self.assertEqual(args, dict(response.data))
        self.assertEqual(1, models.ProductVersion.objects.filter(product_version_id='product-2').count())
        self.assertNumChanges([1])

    def test_create_without_short(self):
        args = {"name": "Our Awesome Product", "version": "2", "product": "product"}
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({'product_version_id': 'product-2',
                     'active': False,
                     'releases': [],
                     'product': 'product',
                     'short': 'product'})
        self.assertDictEqual(args, dict(response.data))
        self.assertEqual(1, models.ProductVersion.objects.filter(product_version_id='product-2').count())
        self.assertNumChanges([1])

    def test_create_with_invalid_short(self):
        args = {"name": "Our Awesome Product", "short": "PRODUCT",
                "version": "2", "product": "product"}
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(0, models.ProductVersion.objects.filter(product_version_id='product-2').count())
        self.assertNumChanges([])
        self.assertIn('Only accept lowercase letters, numbers or -', response.data['short'])

    def test_create_with_extra_field(self):
        args = {"name": "Our Awesome Product", "short": "product",
                "version": "2", "product": "product", "foo": "bar"}
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_create_with_non_existing_product(self):
        args = {"name": "Our Awesome Product", "short": "product",
                "version": "2", "product": "foo"}
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(0, models.ProductVersion.objects.filter(product_version_id='product-2').count())
        self.assertNumChanges([])

    def test_create_duplicate(self):
        args = {"name": "Our Awesome Product", "short": "product",
                "version": "2", "product": "product"}
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get(self):
        response = self.client.get(reverse('productversion-detail', args=["product-1"]))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(dict(response.data), {"product": "product",
                                               "product_version_id": "product-1",
                                               "short": "product",
                                               "name": "Product Version",
                                               "active": False,
                                               "releases": [],
                                               "version": "1"})

    def test_all_for_dummy(self):
        response = self.client.get(reverse('product-detail', args=["dummy"]))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response.data['product_versions'], [])

    def test_all_for_product(self):
        response = self.client.get(reverse('product-detail', args=["product"]))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(set(response.data['product_versions']),
                         set(["product-0", "product-1"]))

    def test_clone(self):
        response = self.client.get(reverse('productversion-detail', args=['product-1']))
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response.data['version'] = 2
        del response.data['product_version_id']
        del response.data['releases']
        del response.data['active']
        response = self.client.post(reverse('productversion-list'), response.data)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(dict(response.data),
                         {'product': 'product', 'product_version_id': 'product-2',
                          'short': 'product', 'name': 'Product Version', 'version': '2',
                          'active': False, 'releases': []})
        self.assertNumChanges([1])

    def test_releases_are_ordered(self):
        release_type = models.ReleaseType.objects.get(short='ga')
        pv = models.ProductVersion.objects.get(product_version_id='product-1')
        for x in range(11, 7, -1):
            models.Release.objects.create(short='product',
                                          name='Product',
                                          version='1.%d' % x,
                                          release_type=release_type,
                                          product_version=pv)
        response = self.client.get(reverse('productversion-detail', args=['product-1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data.get('releases', []),
            ['product-1.8', 'product-1.9', 'product-1.10', 'product-1.11']
        )

    def test_query_with_illegal_active(self):
        response = self.client.get(reverse('productversion-list'), {"active": "abcd"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_multi_values(self):
        response = self.client.get(reverse('productversion-list') +
                                   '?product_version_id=product-1&product_version_id=product-0')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)


class ProductVersionUpdateRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/release/fixtures/tests/product_version.json",
    ]

    def test_update(self):
        response = self.client.put(reverse('productversion-detail', args=['product-1']),
                                   {'short': 'product', 'name': 'TEST PRODUCT',
                                    'version': '1', 'product': 'product'},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.ProductVersion.objects.get(product_version_id='product-1').name,
                         'TEST PRODUCT')
        self.assertNumChanges([1])

    def test_put_as_create_disabled(self):
        args = {'name': 'Product', 'short': 'p', 'version': '1'}
        response = self.client.put(reverse('productversion-detail', args=['p-1']), args)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([])

    def test_update_missing_field(self):
        response = self.client.put(reverse('productversion-detail', args=['product-1']),
                                   {'short': 'product'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_partial(self):
        response = self.client.patch(reverse('productversion-detail', args=['product-1']),
                                     {'name': 'Tcudorp'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(models.ProductVersion.objects.get(product_version_id='product-1').name,
                         'Tcudorp')

    def test_partial_update_empty(self):
        url = reverse('productversion-detail', args=['product-1'])
        response = self.client.patch(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_only_short(self):
        response = self.client.patch(reverse('productversion-detail', args=['product-1']),
                                     {'short': 'tcudorp'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        response = self.client.get(reverse('productversion-detail', args=['product-1']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('productversion-detail', args=['tcudorp-1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_only_version(self):
        response = self.client.patch(reverse('productversion-detail', args=['product-1']),
                                     {'version': '2'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        response = self.client.get(reverse('productversion-detail', args=['product-1']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('productversion-detail', args=['product-2']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_product(self):
        self.client.post(reverse('product-list'), {'short': 'test', 'name': 'Test'}, format='json')
        response = self.client.patch(reverse('productversion-detail', args=['product-1']),
                                     {'product': 'test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1, 1])
        pv = models.ProductVersion.objects.get(product_version_id='product-1')
        self.assertEqual(pv.product.name, 'Test')
        self.assertEqual(pv.short, 'product')

    def test_change_short_on_put_implicitly(self):
        self.client.post(reverse('product-list'), {'short': 'test', 'name': 'Test'}, format='json')
        response = self.client.put(reverse('productversion-detail', args=['product-1']),
                                   {'product': 'test', 'name': 'Test product',
                                    'version': '1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('short'), 'test')
        self.assertEqual(response.data.get('product'), 'test')
        self.assertNumChanges([1, 1])
        pv = models.ProductVersion.objects.get(product_version_id='test-1')
        self.assertEqual(pv.product.name, 'Test')


class ActiveCountTestCase(APITestCase):
    fixtures = ["pdc/apps/release/fixtures/tests/active-filter.json"]

    def test_active_for_product_version_with_mixed(self):
        pv = models.ProductVersion.objects.get(pk=3)
        self.assertTrue(pv.active)
        self.assertEqual(pv.release_count, 2)
        self.assertEqual(pv.active_release_count, 1)

    def test_active_for_product_version_with_active_only(self):
        pv = models.ProductVersion.objects.get(pk=2)
        self.assertTrue(pv.active)
        self.assertEqual(pv.release_count, 1)
        self.assertEqual(pv.active_release_count, 1)

    def test_active_for_product_version_with_inactive_only(self):
        pv = models.ProductVersion.objects.get(pk=4)
        self.assertFalse(pv.active)
        self.assertEqual(pv.release_count, 1)
        self.assertEqual(pv.active_release_count, 0)

    def test_active_for_product_with_mixed(self):
        p = models.Product.objects.get(pk=2)
        self.assertTrue(p.active)
        self.assertEqual(p.product_version_count, 3)
        self.assertEqual(p.active_product_version_count, 2)
        self.assertEqual(p.release_count, 4)
        self.assertEqual(p.active_release_count, 2)

    def test_active_for_product_with_active_only(self):
        p = models.Product.objects.get(pk=1)
        self.assertTrue(p.active)
        self.assertEqual(p.product_version_count, 1)
        self.assertEqual(p.active_product_version_count, 1)
        self.assertEqual(p.release_count, 1)
        self.assertEqual(p.active_release_count, 1)

    def test_active_for_product_with_inactive_only(self):
        p = models.Product.objects.get(pk=3)
        self.assertFalse(p.active)
        self.assertEqual(p.product_version_count, 1)
        self.assertEqual(p.active_product_version_count, 0)
        self.assertEqual(p.release_count, 1)
        self.assertEqual(p.active_release_count, 0)


class ActiveFilterTestCase(APITestCase):
    fixtures = ["pdc/apps/release/fixtures/tests/active-filter.json"]

    def test_filter_active_releases(self):
        response = self.client.get(reverse('release-list') + '?active=True')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(x['release_id'] for x in response.data['results']),
                         set(['x-1.0', 'y-1.0', 'y-2.0']))

    def test_filter_inactive_releases(self):
        response = self.client.get(reverse('release-list') + '?active=False')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(x['release_id'] for x in response.data['results']),
                         set(['y-2.1', 'y-3.0', 'z-1.0']))

    def test_filter_active_product_versions(self):
        response = self.client.get(reverse('productversion-list') + '?active=True')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(x['product_version_id'] for x in response.data['results']),
                         set(['x-1', 'y-1', 'y-2']))

    def test_filter_inactive_product_versions(self):
        response = self.client.get(reverse('productversion-list') + '?active=False')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(x['product_version_id'] for x in response.data['results']),
                         set(['y-3', 'z-1']))

    def test_filter_product_versions_with_invalid_value(self):
        response = self.client.get(reverse('productversion-list') + '?active=foo')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_active_products(self):
        response = self.client.get(reverse('product-list') + '?active=True')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(x['short'] for x in response.data['results']),
                         set(['x', 'y']))

    def test_filter_inactive_products(self):
        response = self.client.get(reverse('product-list') + '?active=False')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(x['short'] for x in response.data['results']),
                         set(['z']))

    def test__filter_products_with_invalid_value(self):
        response = self.client.get(reverse('product-list') + '?active=foo')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReleaseRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/release/fixtures/tests/base_product.json",
        "pdc/apps/release/fixtures/tests/product_version.json",
        "pdc/apps/bindings/fixtures/tests/releasedistgitmapping.json"
    ]

    def test_create_without_product_version(self):
        args = {"name": "Fedora", "short": "f", "version": '20', "release_type": "ga"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({"active": True, 'integrated_with': None,
                     'base_product': None, 'product_version': None, 'compose_set': [],
                     'dist_git': None, 'release_id': 'f-20',
                     'bugzilla': None})
        self.assertEqual(1, models.Release.objects.filter(release_id='f-20').count())
        self.assertEqual(dict(response.data), args)
        self.assertNumChanges([1])

    def test_create_with_bugzilla_mapping(self):
        args = {"name": u"Fedora", "short": u"f", "version": u'20', "release_type": u"ga",
                "bugzilla": {"product": u"Fedora Bugzilla Product"}}
        response = self.client.post(reverse('release-list'), args, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({"active": True, 'integrated_with': None,
                     'base_product': None, 'product_version': None, 'compose_set': [],
                     'dist_git': None, 'release_id': u'f-20'})
        self.assertEqual(ReleaseBugzillaMapping.objects.count(), 1)
        self.assertDictEqual(dict(response.data.pop('bugzilla')), args.pop('bugzilla'))
        self.assertDictEqual(dict(response.data), args)
        self.assertNumChanges([2])

    def test_create_with_dist_git_mapping(self):
        args = {"name": "Fedora", "short": "f", "version": '20', "release_type": "ga",
                "dist_git": {"branch": "dist_git_branch"}}
        response = self.client.post(reverse('release-list'), args, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({"active": True, 'integrated_with': None,
                     'base_product': None, 'product_version': None, 'compose_set': [],
                     'release_id': 'f-20', 'bugzilla': None})
        self.assertEqual(ReleaseDistGitMapping.objects.count(), 2)
        self.assertDictEqual(dict(response.data), args)
        self.assertNumChanges([2])

    def test_create_with_invalid_active(self):
        args = {"name": "Fedora", "short": "f", "version": '20',
                "release_type": "ga", "active": "yes please"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn(u'"yes please" is not a valid boolean', response.data['active'][0])

    def test_create_with_invalid_short(self):
        args = {"name": "Fedora", "short": "F", "version": '20', "release_type": "ga"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertIn('Only accept lowercase letters, numbers or -', response.data['short'])

    def test_create_with_extra_fields(self):
        args = {"name": "Fedora", "short": "f", "version": '20', "release_type": "ga", "foo": "bar"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')

    def test_create_duplicate(self):
        args = {"name": "Fedora", "short": "f", "version": '20', "release_type": "ga"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_create_with_product_version(self):
        args = {"name": "Our Awesome Product", "short": "product", "version": "1.1",
                "release_type": "ga", "product_version": "product-1"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({'product_version': 'product-1',
                     'release_id': 'product-1.1', 'active': True, 'base_product': None,
                     'compose_set': [], 'dist_git': None,
                     'bugzilla': None, 'integrated_with': None})
        self.assertEqual(args, dict(response.data))
        self.assertEqual(1, models.Release.objects.filter(release_id='product-1.1').count())
        self.assertNumChanges([1])
        response = self.client.get(reverse('release-list') + '?product_version=product-1')
        self.assertEqual(1, response.data['count'])

    def test_create_with_base_product(self):
        args = {"name": "Supplementary", "short": "supp", "version": "1.1",
                "release_type": "ga", "base_product": "product-1"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        args.update({'base_product': 'product-1',
                     'active': True, 'compose_set': [], 'dist_git': None,
                     'release_id': 'supp-1.1@product-1', 'product_version': None,
                     'bugzilla': None, 'integrated_with': None})
        self.assertEqual(args, dict(response.data))
        self.assertNumChanges([1])
        response = self.client.get(reverse('release-list') + '?base_product=product-1')
        self.assertEqual(1, response.data['count'])

    def test_create_with_null_integrated_with(self):
        args = {"name": "Fedora", "short": "f", "version": "20", "release_type": "ga", "integrated_with": None}
        response = self.client.post(reverse('release-list'), args, format='json')
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertNumChanges([1])

    def test_update_with_patch_null_dist_git_mapping(self):
        args = {"name": "Fedora", "short": "f", "version": '20', "release_type": "ga"}
        response = self.client.post(reverse('release-list'), args)
        args = {"dist_git": None}
        response = self.client.patch(reverse('release-detail', kwargs={'release_id': 'f-20'}), args, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(ReleaseDistGitMapping.objects.count(), 1)
        self.assertEqual(response.data['dist_git'], None)
        self.assertNumChanges([1])

    def test_update_with_patch_dist_git_mapping_to_null(self):
        args = {"dist_git": None}
        response = self.client.patch(reverse('release-detail',
                                             kwargs={'release_id': 'release-1.0'}),
                                     args, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(ReleaseDistGitMapping.objects.count(), 0)
        self.assertEqual(response.data['dist_git'], None)
        self.assertNumChanges([1])

    def test_query_with_filter(self):
        url = reverse('release-list')
        response = self.client.get(url + '?release_id=release-1.0')
        self.assertEqual(1, response.data['count'])
        response = self.client.get(url + '?name=Test%20Release')
        self.assertEqual(1, response.data['count'])
        response = self.client.get(url + '?short=release')
        self.assertEqual(1, response.data['count'])
        response = self.client.get(url + '?version=1.0')
        self.assertEqual(1, response.data['count'])
        response = self.client.get(url + '?release_type=ga')
        self.assertEqual(1, response.data['count'])
        response = self.client.get(url + '?has_base_product=False')
        self.assertEqual(1, response.data['count'])
        response = self.client.get(url + '?has_base_product=True')
        self.assertEqual(0, response.data['count'])
        response = self.client.get(url + '?bugzilla_product=null')
        self.assertEqual(1, response.data['count'])
        self.test_create_with_bugzilla_mapping()
        response = self.client.get(url + '?bugzilla_product=Fedora Bugzilla Product')
        self.assertEqual(1, response.data['count'])
        response = self.client.get(url + '?dist_git_branch=release_branch')
        self.assertEqual(1, response.data['count'])

    def test_query_unknown_filter(self):
        response = self.client.get(reverse('release-list'), {'foo': 'bar'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual('Unknown query params: foo.', response.data.get('detail'))

    def test_query_illegal_active_filter(self):
        response = self.client.get(reverse('release-list'), {'active': 'abcd'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_with_multi_value_filter(self):
        args = {"name": "Fedora", "short": "f", "version": '20', "release_type": "ga",
                "dist_git": {"branch": "dist_git_branch"}}
        self.client.post(reverse('release-list'), args, format='json')
        url = reverse('release-list')
        response = self.client.get(url + '?release_id=release-1.0&release_id=f-20')
        self.assertEqual(response.data['count'], 2)

    def test_list_ordered(self):
        release_type = models.ReleaseType.objects.get(short='ga')
        for x in range(11, 7, -1):
            models.Release.objects.create(short='product',
                                          name='Product',
                                          version='1.%d' % x,
                                          release_type=release_type)
        response = self.client.get(reverse('release-list'), {'short': 'product'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [x.get('release_id') for x in response.data.get('results', [])],
            ['product-1.8', 'product-1.9', 'product-1.10', 'product-1.11']
        )


class ReleaseCloneTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/bindings/fixtures/tests/releasedistgitmapping.json"
    ]

    def test_clone_new_version(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(2, models.Release.objects.count())
        self.assertEqual(2, models.Variant.objects.count())
        self.assertEqual(2, models.VariantArch.objects.count())
        release = models.Release.objects.latest('id')
        self.assertEqual(release.variant_set.count(), 1)
        self.assertEqual(release.variant_set.all()[0].variantarch_set.count(), 1)
        self.assertDictEqual(response.data,
                             {'short': 'release', 'version': '1.1', 'release_type': 'ga',
                              'name': 'Test Release', 'dist_git': {'branch': 'release_branch'},
                              'product_version': None, 'base_product': None, 'active': True,
                              'release_id': 'release-1.1', 'compose_set': [],
                              'bugzilla': None, 'integrated_with': None})
        self.assertNumChanges([4])

    def test_clone_extra_fields(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1', 'foo': 'bar'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertNumChanges([])

    def test_clone_bad_variant_format_no_period(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_trees': ['sparkly-unicorn']},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.Release.objects.filter(release_id='release-1.1').count(),
                         0)

    def test_clone_bad_variant_format_two_periods(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_trees': ['ponies.and.rainbows']},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.Release.objects.filter(release_id='release-1.1').count(),
                         0)

    def test_clone_bad_variant_format_not_a_list(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_trees': ''},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not a list', response.data['detail'][0])
        self.assertNumChanges([])
        self.assertEqual(models.Release.objects.filter(release_id='release-1.1').count(),
                         0)
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_trees': 'not-a-list'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not a list', response.data['detail'][0])
        self.assertNumChanges([])
        self.assertEqual(models.Release.objects.filter(release_id='release-1.1').count(),
                         0)

    def test_clone_variant_not_in_original(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_trees': ['Foo.Bar']},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.Release.objects.filter(release_id='release-1.1').count(),
                         0)

    def test_clone_with_filter_variants(self):
        v = models.Variant.objects.create(
            release=models.Release.objects.get(release_id='release-1.0'),
            variant_uid='Client',
            variant_id='Client',
            variant_name='Client',
            variant_type=models.VariantType.objects.get(name='variant'),
        )
        models.VariantArch.objects.create(variant=v, arch_id=1)
        models.VariantArch.objects.create(
            variant=models.Variant.objects.get(variant_uid='Server'),
            arch_id=1
        )
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_trees': ['Server.x86_64']},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(2, models.Release.objects.count())
        self.assertEqual(3, models.Variant.objects.count())
        self.assertEqual(4, models.VariantArch.objects.count())
        release = models.Release.objects.latest('id')
        self.assertEqual(release.variant_set.count(), 1)
        self.assertEqual(release.variant_set.all()[0].variantarch_set.count(), 1)
        self.assertItemsEqual(release.trees, ['Server.x86_64'])
        self.assertNumChanges([4])

    def test_clone_with_explicit_empty_trees(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'include_trees': []},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(2, models.Release.objects.count())
        self.assertEqual(1, models.Variant.objects.count())
        self.assertEqual(1, models.VariantArch.objects.count())
        release = models.Release.objects.latest('id')
        self.assertEqual(release.variant_set.count(), 0)
        self.assertDictEqual(response.data,
                             {'short': 'release', 'version': '1.1', 'release_type': 'ga',
                              'name': 'Test Release', 'dist_git': {'branch': 'release_branch'},
                              'product_version': None, 'base_product': None, 'active': True,
                              'release_id': 'release-1.1', 'compose_set': [],
                              'bugzilla': None, 'integrated_with': None})
        self.assertNumChanges([2])

    def test_clone_not_unique(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'active': False},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(1, models.Release.objects.count())
        self.assertNumChanges([])

    def test_clone_missing_old_release_id(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'foo': 'bar'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(1, models.Release.objects.count())

    def test_clone_bad_param(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'product_version': 'no'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(1, models.Release.objects.count())

    def test_clone_non_existing_release(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-2.0', 'version': '2.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(1, models.Release.objects.count())
        self.assertNumChanges([])

    def test_clone_create_bugzilla_mapping(self):
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'bugzilla': {'product': 'Test Release 1'}},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('bugzilla', {}).get('product'),
                         'Test Release 1')
        self.assertEqual(1, ReleaseBugzillaMapping.objects.count())
        self.assertNumChanges([5])

    def test_clone_old_bugzilla_mapping(self):
        ReleaseBugzillaMapping.objects.create(
            release=models.Release.objects.get(release_id='release-1.0'),
            bugzilla_product='Test Release 1'
        )
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('bugzilla', {}).get('product'),
                         'Test Release 1')
        self.assertEqual(2, ReleaseBugzillaMapping.objects.count())
        self.assertNumChanges([5])

    def test_clone_remove_bugzilla_mapping(self):
        ReleaseBugzillaMapping.objects.create(
            release=models.Release.objects.get(release_id='release-1.0'),
            bugzilla_product='Test Release 1'
        )
        response = self.client.post(reverse('releaseclone-list'),
                                    {'old_release_id': 'release-1.0', 'version': '1.1',
                                     'bugzilla': None},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('bugzilla'), None)
        self.assertEqual(1, ReleaseBugzillaMapping.objects.count())
        self.assertNumChanges([4])


class ReleaseRPMMappingViewSetTestCase(APITestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def test_get_for_single_compose(self):
        expected_data = {
            'compose': 'compose-1',
            'mapping': {
                'Server': {
                    'x86_64': {
                        'bash': ['x86_64'],
                    }
                }
            }
        }
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['release-1.0', 'bash']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_get_for_no_compose(self):
        compose_models.Compose.objects.filter(release__release_id='product-1.0').delete()
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['product-1.0', 'bash']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_for_no_compose_without_include(self):
        compose_models.Compose.objects.filter(release__release_id='release-1.0').delete()
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['release-1.0', 'bash']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_for_no_compose_with_include(self):
        override = compose_models.OverrideRPM.objects.get(id=1)
        override.include = True
        override.save()

        compose_models.Compose.objects.filter(release__release_id='release-1.0').delete()
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['release-1.0', 'bash']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"compose": None, "mapping": {"Server": {"x86_64": {"bash-doc": ["x86_64"]}}}})

    def test_get_for_nonexisting_release(self):
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['product-1.1', 'bash']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_for_nonexisting_package(self):
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['product-1.0', 'ponies']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_for_more_compose(self):
        # There is compose-1 with some rpms, and newer ComposeWithNoRPMs with
        # no rpms. The view grabs the newest mapping, finds there is nothing to
        # show as mapping and returns 404.
        release = models.Release.objects.get(release_id='release-1.0')
        compose_models.Compose.objects.create(
            release=release,
            compose_respin=0,
            compose_date='2015-01-30',
            compose_id='ComposeWithNoRPMs',
            compose_type=compose_models.ComposeType.objects.get(name='production'),
            acceptance_testing=compose_models.ComposeAcceptanceTestingState.objects.get(name='untested'),
        )
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['release-1.0', 'ponies']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_options_on_list_url(self):
        response = self.client.options(reverse('release-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ReleaseUpdateRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/release/fixtures/tests/release.json',
        "pdc/apps/bindings/fixtures/tests/releasedistgitmapping.json"
    ]

    def setUp(self):
        self.url = reverse('release-detail', args=['release-1.0'])
        self.release = models.Release.objects.get(release_id='release-1.0')
        self.serialized_release = {
            'short': 'release',
            'version': '1.0',
            'name': 'Test Release',
            'active': True,
            'dist_git': {'branch': 'release_branch'},
            'release_type': 'ga'
        }

    def test_update(self):
        response = self.client.put(self.url,
                                   {'short': 'product', 'version': '1.0', 'release_type': 'ga',
                                    'name': 'Our Product'},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), 'Our Product')
        self.assertEqual(models.Release.objects.get(release_id='product-1.0').name,
                         'Our Product')
        self.assertNumChanges([2])

    def test_partial_update_empty(self):
        url = reverse('release-detail', args=['product-1.0'])
        response = self.client.patch(url, format='json', data={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_missing_optional_fields_are_erased(self):
        self.release.product_version = models.ProductVersion.objects.create(
            product=models.Product.objects.create(short='p', name='Product'),
            short='p',
            version=1,
            name='Product Version'
        )
        release_type = models.ReleaseType.objects.get(short="ga")
        self.release.base_product = models.BaseProduct.objects.create(
            name='Base Product',
            short='bp',
            version='1',
            release_type=release_type,
        )
        self.release.save()

        response = self.client.put(reverse('release-detail', args=[self.release.release_id]),
                                   {'short': 'release',
                                    'version': '3.0',
                                    'release_type': 'ga',
                                    'name': 'update',
                                    },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('release_id'), 'release-3.0')
        self.assertIsNone(response.data.get('base_product'))
        self.assertIsNone(response.data.get('product_version'))
        self.assertIsNone(response.data.get('dist_git'))
        self.assertIsNone(response.data.get('bugzilla'))
        self.assertIsNone(response.data.get('integrated_with'))
        self.assertEqual(response.data.get('active'), True)
        release = models.Release.objects.get(release_id='release-3.0')
        self.assertIsNone(release.dist_git_branch)
        self.assertIsNone(release.base_product)
        self.assertIsNone(release.product_version)
        self.assertNumChanges([2])

    def test_update_can_explicitly_erase_optional_field(self):
        response = self.client.put(self.url,
                                   {'short': 'release', 'version': '1.0', 'release_type': 'ga',
                                    'name': 'Test Release', 'dist_git': None},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get('dist_git'))
        self.assertIsNone(models.Release.objects.get(release_id='release-1.0').dist_git_branch)
        self.assertNumChanges([1])

    def test_update_can_reset_base_product(self):
        release_type = models.ReleaseType.objects.get(short="ga")
        self.release.base_product = models.BaseProduct.objects.create(
            name='Base Product',
            short='bp',
            version='1',
            release_type=release_type,
        )
        self.release.save()

        response = self.client.patch(reverse('release-detail', args=['release-1.0@bp-1']),
                                     {'base_product': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The dist-git mapping mentioned in changelog because release_id changes.
        self.assertNumChanges([2])
        self.assertIsNone(response.data['base_product'])
        release = models.Release.objects.get(release_id='release-1.0')
        self.assertIsNone(release.base_product)

    def test_update_can_reset_product_version(self):
        self.release.product_version = models.ProductVersion.objects.create(
            name='Base Product',
            short='p',
            version='1',
            product=models.Product.objects.create(name='Product', short='p')
        )
        self.release.save()

        response = self.client.patch(reverse('release-detail', args=['release-1.0']),
                                     {'product_version': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertIsNone(response.data['product_version'])
        release = models.Release.objects.get(release_id='release-1.0')
        self.assertIsNone(release.product_version)

    def test_update_can_explicitly_erase_optional_field_via_patch(self):
        response = self.client.patch(self.url, {'dist_git': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get('dist_git'))
        self.assertIsNone(models.Release.objects.get(release_id='release-1.0').dist_git_branch)
        self.assertNumChanges([1])

    def test_update_single_field(self):
        response = self.client.patch(self.url, {'active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('active'))
        self.assertFalse(models.Release.objects.get(release_id='release-1.0').active)
        self.assertNumChanges([1])

    def test_update_product_version(self):
        self.client.post(reverse('product-list'),
                         {'name': 'Test Release', 'short': 'release'},
                         format='json')
        self.client.post(reverse('productversion-list'),
                         {'name': 'Test Release', 'short': 'release', 'version': '1', 'product': 'release'},
                         format='json')
        response = self.client.patch(self.url, {'product_version': 'release-1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('product_version'), 'release-1')
        self.assertNumChanges([1, 1, 1])
        response = self.client.get(reverse('productversion-detail', args=['release-1']))
        self.assertItemsEqual(response.data.get('releases'), ['release-1.0'])

    def test_update_to_change_release_id(self):
        response = self.client.patch(self.url, {'release_type': 'eus'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('release_type'), 'eus')
        self.assertEqual(response.data.get('release_id'), 'release-1.0-eus')
        # Dist git mapping is not changed as such, only its readable
        # representation returned by export().
        self.assertNumChanges([2])
        response = self.client.get(reverse('release-detail', args=['release-1.0']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('release-detail', args=['release-1.0-eus']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_bugzilla_mapping(self):
        response = self.client.patch(self.url,
                                     {'bugzilla': {'product': 'Test Product'}},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('bugzilla', {}).get('product'),
                         'Test Product')
        self.assertEqual(ReleaseBugzillaMapping.objects.get(release__release_id='release-1.0').bugzilla_product,
                         'Test Product')
        self.assertNumChanges([1])

    def test_update_bugzilla_mapping(self):
        ReleaseBugzillaMapping.objects.create(release=self.release, bugzilla_product='Old product')
        response = self.client.patch(self.url, {'bugzilla': {'product': 'New product'}}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('bugzilla', {}).get('product'), 'New product')
        self.assertEqual(ReleaseBugzillaMapping.objects.get(release__release_id='release-1.0').bugzilla_product,
                         'New product')
        self.assertNumChanges([1])

    def test_remove_bugzilla_mapping(self):
        ReleaseBugzillaMapping.objects.create(release=self.release, bugzilla_product='Old product')
        self.serialized_release['bugzilla'] = None
        response = self.client.put(self.url, self.serialized_release, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('bugzilla'), None)
        response = self.client.get(reverse('release-detail', args=['product-1.0']))
        self.assertEqual(response.data.get('bugzilla'), None)
        self.assertEqual(ReleaseBugzillaMapping.objects.filter(release__release_id='product-1.0').count(), 0)
        self.assertNumChanges([1])

    def test_remove_bugzilla_mapping_and_switch_active(self):
        ReleaseBugzillaMapping.objects.create(release=self.release, bugzilla_product='Old product')
        self.serialized_release['bugzilla'] = None
        self.serialized_release['active'] = False
        response = self.client.put(self.url, self.serialized_release, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('bugzilla'), None)
        self.assertFalse(response.data.get('active'))
        response = self.client.get(reverse('release-detail', args=['product-1.0']))
        self.assertEqual(response.data.get('bugzilla'), None)
        self.assertFalse(response.data.get('active'))
        self.assertEqual(ReleaseBugzillaMapping.objects.filter(release__release_id='product-1.0').count(), 0)
        self.assertNumChanges([2])

    def test_missing_bugzilla_mapping_should_be_removed(self):
        ReleaseBugzillaMapping.objects.create(release=self.release, bugzilla_product='Old product')
        response = self.client.put(self.url, self.serialized_release, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data.get('bugzilla'))
        response = self.client.get(reverse('release-detail', args=['product-1.0']))
        self.assertIsNone(response.data.get('bugzilla'))
        self.assertEqual(ReleaseBugzillaMapping.objects.filter(release__release_id='product-1.0').count(), 0)
        self.assertNumChanges([1])

    def test_put_as_create_is_disabled(self):
        response = self.client.put(reverse('release-detail', args=['i-do-not-exist']),
                                   {'short': 'test',
                                    'version': '3.1',
                                    'release_type': 'ga',
                                    'name': 'release'},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([])

    def test_update_bugzilla_with_wrong_field(self):
        response = self.client.patch(reverse('release-detail', args=[self.release.release_id]),
                                     {'bugzilla': {'king': 'Richard III.'}},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Unknown fields: "king".'})
        self.assertNumChanges([])

    def test_update_dist_git_with_wrong_field(self):
        response = self.client.patch(reverse('release-detail', args=[self.release.release_id]),
                                     {'dist_git': {'leaf': 'maple'}},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'detail': 'Unknown fields: "leaf".'})
        self.assertNumChanges([])

    def test_patch_integrated_with(self):
        models.Release.objects.create(short='release', version='2.0', name='Test release',
                                      release_type=self.release.release_type)
        response = self.client.patch(reverse('release-detail', args=[self.release.release_id]),
                                     {'integrated_with': 'release-2.0'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('integrated_with'), 'release-2.0')
        self.assertNumChanges([1])


class ReleaseLatestComposeTestCase(APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
    ]

    def setUp(self):
        self.release = models.Release.objects.get(release_id='release-1.0')
        self.ct_test = compose_models.ComposeType.objects.get(name='test')
        self.ct_prod = compose_models.ComposeType.objects.get(name='production')
        self.ct_nightly = compose_models.ComposeType.objects.get(name='nightly')
        self.untested = compose_models.ComposeAcceptanceTestingState.objects.get(name='untested')

    def test_compare_by_date(self):
        compose_models.Compose.objects.create(compose_respin=0,
                                              compose_date='2015-02-10',
                                              compose_type=self.ct_test,
                                              compose_id='compose-1',
                                              release=self.release,
                                              acceptance_testing=self.untested)
        compose_models.Compose.objects.create(compose_respin=0,
                                              compose_date='2015-02-09',
                                              compose_type=self.ct_test,
                                              compose_id='compose-2',
                                              release=self.release,
                                              acceptance_testing=self.untested)
        latest = self.release.get_latest_compose()
        self.assertEqual(latest.compose_id, 'compose-1')

    def test_compare_by_date_then_respin(self):
        compose_models.Compose.objects.create(compose_respin=1,
                                              compose_date='2015-02-09',
                                              compose_type=self.ct_test,
                                              compose_id='compose-1',
                                              release=self.release,
                                              acceptance_testing=self.untested)
        compose_models.Compose.objects.create(compose_respin=0,
                                              compose_date='2015-02-09',
                                              compose_type=self.ct_test,
                                              compose_id='compose-2',
                                              release=self.release,
                                              acceptance_testing=self.untested)
        latest = self.release.get_latest_compose()
        self.assertEqual(latest.compose_id, 'compose-1')

    def test_compare_by_date_then_respin_then_compose_type(self):
        compose_models.Compose.objects.create(compose_respin=0,
                                              compose_date='2015-02-09',
                                              compose_type=self.ct_prod,
                                              compose_id='compose-1',
                                              release=self.release,
                                              acceptance_testing=self.untested)
        compose_models.Compose.objects.create(compose_respin=0,
                                              compose_date='2015-02-09',
                                              compose_type=self.ct_test,
                                              compose_id='compose-2',
                                              release=self.release,
                                              acceptance_testing=self.untested)
        latest = self.release.get_latest_compose()
        self.assertEqual(latest.compose_id, 'compose-1')


class ReleaseComposeLinkingTestCase(APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/compose_release_linking.json",
    ]

    def test_linking_visible_in_rest(self):
        response = self.client.get(reverse('release-detail', args=['product-1.0-eus']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data.get('compose_set'),
                              ['compose-1'])
        response = self.client.get(reverse('release-detail', args=['product-1.0']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data.get('compose_set'),
                              ['compose-1', 'compose-2'])
        response = self.client.get(reverse('release-detail', args=['product-1.0-updates']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data.get('compose_set'),
                              ['compose-1', 'compose-2'])

    def test_linking_visible_in_web_ui(self):
        client = Client()
        response = client.get('/compose/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('product-1.0', str(response))
        self.assertIn('product-1.0-updates', str(response))
        self.assertIn('product-1.0-eus', str(response))

        response = client.get('/compose/2/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('product-1.0', str(response))
        self.assertIn('product-1.0-updates', str(response))
        self.assertNotIn('product-1.0-eus', str(response))

    def test_release_rpm_mapping_only_includes_variants_from_release(self):
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['product-1.0-updates', 'bash']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data,
                             {'compose': 'compose-1',
                              'mapping': {'Server': {'x86_64': {'bash': ['x86_64']}}}})

    def test_release_rpm_mapping_uses_overrides_from_linked_release(self):
        response = self.client.get(reverse('releaserpmmapping-detail',
                                   args=['product-1.0-eus', 'bash']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data,
                             {'compose': 'compose-1',
                              'mapping': {'Server': {'x86_64': {'bash': ['x86_64'],
                                                                'bash-doc': ['x86_64']},
                                                     'src': {'bash': ['x86_64']}},
                                          'Client': {'x86_64': {'bash': ['x86_64']}}}})


class ReleaseImportTestCase(TestCaseWithChangeSetMixin, APITestCase):
    def test_import_correct_data(self):
        with open('pdc/apps/release/fixtures/tests/composeinfo-0.3.json', 'r') as f:
            data = json.loads(f.read())
        response = self.client.post(reverse('releaseimportcomposeinfo-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('url'), '/rest_api/v1/releases/tp-1.0/')
        self.assertNumChanges([11])
        self.assertEqual(models.Product.objects.count(), 2)
        self.assertEqual(models.ProductVersion.objects.count(), 2)
        self.assertEqual(models.Release.objects.count(), 2)
        self.assertEqual(models.Variant.objects.count(), 4)
        self.assertEqual(models.VariantArch.objects.count(), 6)
        self.assertEqual(models.BaseProduct.objects.count(), 1)

        response = self.client.get(reverse('product-detail', args=['tp']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('product_versions'), ['tp-1'])
        response = self.client.get(reverse('productversion-detail', args=['tp-1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('releases'), ['tp-1.0'])
        response = self.client.get(reverse('release-detail', args=['tp-1.0']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(dict(response.data),
                             {'short': 'tp', 'release_id': 'tp-1.0', 'version': '1.0',
                              'name': 'Test Product', 'product_version': 'tp-1',
                              'base_product': None, 'compose_set': [],
                              'integrated_with': None, 'bugzilla': None,
                              'active': True, 'release_type': 'ga', 'dist_git': None})
        release = models.Release.objects.get(release_id='tp-1.0')
        self.assertItemsEqual(release.trees,
                              ['Client.x86_64', 'Server.x86_64', 'Server.s390x',
                               'Server.ppc64', 'Server-SAP.x86_64'])
        self.assertEqual(release.variant_set.get(variant_uid='Server-SAP').integrated_from.release_id,
                         'sap-1.0@tp-1')

        response = self.client.get(reverse('product-detail', args=['sap']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('product_versions'), ['sap-1'])
        response = self.client.get(reverse('productversion-detail', args=['sap-1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('releases'), ['sap-1.0@tp-1'])
        response = self.client.get(reverse('release-detail', args=['sap-1.0@tp-1']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(dict(response.data),
                             {'short': 'sap', 'release_id': 'sap-1.0@tp-1', 'version': '1.0',
                              'name': 'SAP', 'product_version': 'sap-1',
                              'base_product': 'tp-1', 'compose_set': [],
                              'integrated_with': 'tp-1.0', 'bugzilla': None,
                              'active': True, 'release_type': 'ga', 'dist_git': None})
        release = models.Release.objects.get(release_id='sap-1.0@tp-1')
        self.assertItemsEqual(release.trees, ['Server-SAP.x86_64'])
        self.assertEqual(release.variant_set.get(variant_uid='Server-SAP').integrated_to.release_id,
                         'tp-1.0')

        response = self.client.post(reverse('releaseimportcomposeinfo-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('url'), '/rest_api/v1/releases/tp-1.0/')

    def test_import_via_get(self):
        data = {'garbage': 'really'}
        response = self.client.get(reverse('releaseimportcomposeinfo-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_import_garbage(self):
        data = {'garbage': 'really'}
        response = self.client.post(reverse('releaseimportcomposeinfo-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_incorrect_layered_product_version_mismatch(self):
        with open('pdc/apps/release/fixtures/tests/composeinfo-0.3.json', 'r') as f:
            data = json.loads(f.read())
        # Import version 1.0
        response = self.client.post(reverse('releaseimportcomposeinfo-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Bump release version and import again. Note that layered product
        # version remained the same.
        data['payload']['product']['version'] = '1.1'

        response = self.client.post(reverse('releaseimportcomposeinfo-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('version mismatch', response.content)
        self.assertIn('sap-1.0@tp-1', response.content)


class ReleaseTypeTestCase(TestCaseWithChangeSetMixin, APITestCase):
    def test_list(self):
        response = self.client.get(reverse("releasetype-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)

    def test_filter(self):
        response = self.client.get(reverse("releasetype-list"), data={"name": "re"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(reverse("releasetype-list"), data={"short": "ga"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_multi_value(self):
        response = self.client.get(reverse("releasetype-list") + '?short=ga&short=updates')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)


class VariantRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/variants_standalone.json",
    ]

    def test_create(self):
        args = {
            'uid': 'Variant-UID',
            'id': 'Variant-ID',
            'release': 'release-1.0',
            'name': 'Variant',
            'type': 'variant',
            'arches': ['x86_64']
        }
        response = self.client.post(reverse('variant-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected = args.copy()
        expected.update({
            'arches': ['x86_64'],
            'variant_version': None,
            'variant_release': None,
        })
        self.assertEqual(response.data, expected)
        self.assertNumChanges([1])
        self.assertEqual(models.Variant.objects.count(), 3)
        self.assertEqual(models.VariantArch.objects.count(), 5)

    def test_create_missing_fields(self):
        args = {
            'release': 'release-1.0',
            'name': 'Variant',
            'type': 'variant'
        }
        response = self.client.post(reverse('variant-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.Variant.objects.count(), 2)
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_create_bad_release(self):
        args = {
            'uid': 'Variant-UID',
            'id': 'Variant-ID',
            'release': 'release-2.0',
            'name': 'Variant',
            'type': 'variant',
            'arches': ['x86_64'],
        }
        response = self.client.post(reverse('variant-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.Variant.objects.count(), 2)
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_create_bad_variant_type(self):
        args = {
            'uid': 'Variant-UID',
            'id': 'Variant-ID',
            'release': 'release-1.0',
            'name': 'Variant',
            'type': 'bad-type',
            'arches': ['x86_64'],
        }
        response = self.client.post(reverse('variant-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.Variant.objects.count(), 2)
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_create_duplicit(self):
        args = {
            'uid': 'Server-UID',
            'id': 'Server',
            'release': 'release-1.0',
            'name': 'Server name',
            'type': 'variant',
            'arches': ['x86_64'],
        }
        response = self.client.post(reverse('variant-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.Variant.objects.count(), 2)
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_create_extra_fields(self):
        args = {
            'uid': 'Server-UID',
            'id': 'Server',
            'release': 'release-1.0',
            'name': 'Server name',
            'type': 'variant',
            'arches': ['x86_64'],
            'foo': 'bar',
        }
        response = self.client.post(reverse('variant-list'), args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(response.data.get('detail'), 'Unknown fields: "foo".')
        self.assertEqual(models.Variant.objects.count(), 2)
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_list(self):
        response = self.client.get(reverse('variant-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_id(self):
        response = self.client.get(reverse('variant-list'), {'id': 'Server'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_uid(self):
        response = self.client.get(reverse('variant-list'), {'uid': 'Server-UID'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_name(self):
        response = self.client.get(reverse('variant-list'), {'name': 'Server name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_type(self):
        response = self.client.get(reverse('variant-list'), {'type': 'variant'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_filter_release(self):
        response = self.client.get(reverse('variant-list'), {'release': 'foo'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_update(self):
        args = {
            'uid': u'Workstation-UID',
            'id': u'Workstation',
            'release': u'release-1.0',
            'name': u'Workstation variant',
            'type': u'variant',
            'arches': ['ppc64', 'x86_64'],
            'variant_version': None,
            'variant_release': None,
        }
        response = self.client.put(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data.pop('arches'), args.pop('arches'))
        self.assertDictEqual(dict(response.data), args)
        self.assertNumChanges([1])

    def test_update_missing_field(self):
        args = {
            'uid': 'Workstation-UID',
            'release': 'release-1.0',
            'name': 'Workstation variant',
            'type': 'variant',
            'arches': ['ppc64', 'x86_64'],
        }
        response = self.client.put(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_update_bad_release(self):
        args = {
            'uid': 'Workstation-UID',
            'id': 'Workstation',
            'release': 'release-1.0',
            'name': 'Workstation variant',
            'type': 'variant',
            'arches': ['ppc64', 'x86_64'],
        }
        response = self.client.put(reverse('variant-detail', args=['release-2.0/foo']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNumChanges([])

    def test_patch(self):
        args = {
            'name': 'Workstation variant',
        }
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], args['name'])
        self.assertNumChanges([1])

    def test_patch_bad_variant_type(self):
        args = {
            'type': 'whatever',
        }
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_patch_change_arches(self):
        args = {'arches': ['ia64']}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['arches'], ['ia64'])
        self.assertNumChanges([1])

    def test_patch_add_arches(self):
        args = {'add_arches': ['ia64']}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['arches'], ['ia64', 'ppc64', 'x86_64'])
        self.assertNumChanges([1])
        self.assertEqual(models.VariantArch.objects.count(), 5)

    def test_patch_add_duplicit_arches(self):
        args = {'add_arches': ['x86_64']}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_patch_remove_arches(self):
        args = {'remove_arches': ['ppc64']}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['arches'], ['x86_64'])
        self.assertNumChanges([1])
        self.assertEqual(models.VariantArch.objects.count(), 3)

    def test_patch_add_and_remove_arches(self):
        args = {'remove_arches': ['ppc64'], 'add_arches': ['ia64']}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['arches'], ['ia64', 'x86_64'])
        self.assertNumChanges([1])
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_patch_can_not_set_and_add_or_remove_arches(self):
        args = {'arches': ['ppc64'], 'add_arches': ['ia64']}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])
        self.assertEqual(models.VariantArch.objects.count(), 4)

    def test_patch_bad_arch_value(self):
        args = {'arches': ['foo']}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        args = {'arches': [{'this': ['is', 'not', 'a', 'string']}]}
        response = self.client.patch(reverse('variant-detail', args=['release-1.0/Server-UID']),
                                     args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNumChanges([])

    def test_retrieve(self):
        response = self.client.get(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            'uid': 'Server-UID',
            'id': 'Server',
            'release': 'release-1.0',
            'name': 'Server name',
            'type': 'variant',
            'variant_version': None,
            'variant_release': None,
        }
        self.assertItemsEqual(response.data.pop('arches'), ['x86_64', 'ppc64'])
        self.assertDictEqual(dict(response.data), expected)

    def test_retrieve_non_existing(self):
        response = self.client.get(reverse('variant-detail', args=['release-1.0/foo']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(reverse('variant-detail', args=['release-2.0/foo']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # It is impossible to construct following URL directly by reverse
        response = self.client.get(reverse('variant-list') + 'abc-def')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete(self):
        response = self.client.delete(reverse('variant-detail', args=['release-1.0/Server-UID']))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Variant.objects.count(), 1)
        self.assertNumChanges([1])

    def test_delete_non_existing(self):
        response = self.client.delete(reverse('variant-detail', args=['release-1.0/foo']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.delete(reverse('variant-detail', args=['release-2.0/foo']))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bulk_delete(self):
        response = self.client.delete(reverse('variant-list'),
                                      ['release-1.0/Client-UID', 'release-1.0/Server-UID'],
                                      format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.Variant.objects.count(), 0)
        self.assertNumChanges([2])

    def test_bulk_delete_bad_identifier(self):
        response = self.client.delete(reverse('variant-list'),
                                      ['/release-1.0/Client-UID'],
                                      format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data,
                         {'detail': 'Not found.',
                          'id_of_invalid_data': '/release-1.0/Client-UID'})
        self.assertEqual(models.Variant.objects.count(), 2)
        self.assertNumChanges([])

    def test_bulk_partial_update_empty_data(self):
        response = self.client.patch(reverse('variant-list'),
                                     {'release-1.0/Server-UID': {}},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'detail': 'Partial update with no changes does not make much sense.',
                          'id_of_invalid_data': 'release-1.0/Server-UID'})
        self.assertNumChanges([])


class ReleaseGroupRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):

    fixtures = [
        "pdc/apps/release/fixtures/tests/release_group_types.json",
        "pdc/apps/release/fixtures/tests/release_groups.json",
        "pdc/apps/release/fixtures/tests/release.json"
    ]

    def test_list(self):
        url = reverse("releasegroups-list")
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_with_name(self):
        response = self.client.get(reverse("releasegroups-detail", args=["rhel_test"]))
        expect_result = {'active': True, 'type': u'Async',
                         'name': u'rhel_test', 'releases': [u'release-1.0'],
                         'description': u'test'}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expect_result)

    def test_override_ordering_by_description_key(self):
        response = self.client.get(reverse("releasegroups-list"), format='json')
        expect_result = {'active': True, 'type': u'Async',
                         'name': u'rhel_test', 'releases': [u'release-1.0'],
                         'description': u'test'}
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEquals(response.data.get('results')[0], expect_result)
        response1 = self.client.get(reverse("releasegroups-list"), {'ordering': 'description'},
                                    format='json')
        expect_result1 = {'active': True, 'type': u'QuarterlyUpdate',
                          'name': u'rhel_test1', 'releases': [u'release-1.0'],
                          'description': u'good'}
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEquals(response1.data.get('results')[0], expect_result1)

    def test_override_ordering_with_both_character(self):
        response = self.client.get(reverse("releasegroups-list"), format='json')
        expect_result = {'active': True, 'type': u'Async',
                         'name': u'rhel_test', 'releases': [u'release-1.0'],
                         'description': u'test'}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get('results')[0], expect_result)

        url = reverse("releasegroups-list")
        response = self.client.get(url + '?ordering=type,-description')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get('results')[0], expect_result)

        response = self.client.get(url + '?ordering=description,-type')
        expect_result = {'active': True, 'type': u'QuarterlyUpdate',
                         'name': u'rhel_test1', 'releases': [u'release-1.0'],
                         'description': u'good'}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get('results')[0], expect_result)

    def test_retrieve_with_description_para(self):
        response = self.client.get(reverse("releasegroups-detail", args=["rhel_test"]),
                                   args={'description': 'good'}, format='json')
        expect_result = {'active': True, 'type': u'Async',
                         'name': u'rhel_test', 'releases': [u'release-1.0'],
                         'description': u'test'}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expect_result)

    def test_create(self):
        args = {'type': 'Zstream', 'name': 'test', 'description': 'test_create',
                'releases': [u'release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])

    def test_create_without_name(self):
        args = {'type': 'Zstream', 'description': 'test_create',
                'releases': [u'release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_duplicate_name(self):
        args = {'type': 'Zstream', 'name': 'test', 'description': 'test_create',
                'releases': [u'release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        args = {'type': 'QuarterlyUpdate', 'name': 'test', 'description': 'test',
                'releases': [u'release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_error_type(self):
        args = {'type': 'stream', 'name': 'test', 'description': 'test_create',
                'releases': ['release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_without_type(self):
        args = {'name': 'test', 'description': 'test_create',
                'releases': [u'release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_without_description(self):
        args = {'type': 'Zstream', 'name': 'test', 'releases': [u'release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_error_key(self):
        args = {'Error_key': 'test', 'type': 'Zstream', 'name': 'test', 'description': 'test_create',
                'releases': [u'release-1.0']}
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_create(self):
        args1 = {'type': 'Zstream', 'name': 'test_bulk1', 'description': 'test1',
                 'releases': [u'release-1.0']}
        args2 = {'type': 'Zstream', 'name': 'test_bulk2', 'description': 'test2',
                 'releases': [u'release-1.0']}
        args = [args1, args2]
        url = reverse("releasegroups-list")
        response = self.client.post(url, args, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([2])

    def test_update(self):
        args = {'type': 'QuarterlyUpdate', 'name': 'test_update', 'description': 'good',
                'releases': [u'release-1.0']}
        response = self.client.put(reverse("releasegroups-detail", args=['rhel_test']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])

    def test_bulk_update(self):
        args1 = {'type': 'Zstream', 'name': 'test_update1', 'description': 'test1'}
        args2 = {'type': 'Zstream', 'name': 'test_update2', 'description': 'test2'}
        data = {'rhel_test': args1, 'rhel_test1': args2}
        response = self.client.put(reverse("releasegroups-list"), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([2])

    def test_update_without_type(self):
        self.test_create()
        args = {'name': 'test_update', 'description': 'good',
                'releases': [u'release-1.0']}
        response = self.client.put(reverse("releasegroups-detail", args=['test']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_without_name(self):
        self.test_create()
        args = {'type': 'QuarterlyUpdate', 'description': 'good',
                'releases': [u'release-1.0']}
        response = self.client.put(reverse("releasegroups-detail", args=['test']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_without_description(self):
        self.test_create()
        args = {'type': 'QuarterlyUpdate', 'name': 'test_update',
                'releases': [u'release-1.0']}
        response = self.client.put(reverse("releasegroups-detail", args=['test']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_with_error_release(self):
        args = {'type': 'QuarterlyUpdate', 'name': 'test_update', 'description': 'good',
                'releases': [u'release']}
        response = self.client.put(reverse("releasegroups-detail", args=['rhel_test']),
                                   args, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete(self):
        response = self.client.delete(reverse('releasegroups-detail', args=['rhel_test']))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.ReleaseGroup.objects.count(), 1)
        self.assertNumChanges([1])

    def test_bulk_delete(self):
        response = self.client.delete(reverse('releasegroups-list'),
                                      ['rhel_test', 'rhel_test1'], format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(models.ReleaseGroup.objects.count(), 0)
        self.assertNumChanges([2])


class ReleaseLastModifiedResponseTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/release/fixtures/tests/base_product.json",
        "pdc/apps/release/fixtures/tests/product_version.json",
        "pdc/apps/bindings/fixtures/tests/releasedistgitmapping.json"
    ]

    def _get_last_modified_epoch(self, response):
        time_str = response.get('Last-Modified')
        temp_time = time.strptime(time_str, "%a, %d %b %Y %H:%M:%S %Z")
        return int(time.mktime(temp_time))

    def test_after_create_last_modified_time_should_change(self):
        response = self.client.get(reverse('release-list') + '?active=True')
        before_time = self._get_last_modified_epoch(response)
        time.sleep(2)

        args = {"name": "Fedora", "short": "f", "version": '20', "release_type": "ga"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(reverse('release-list') + '?active=True')
        after_time = self._get_last_modified_epoch(response)
        self.assertGreaterEqual(after_time - before_time, 2)

        response = self.client.get(reverse('release-detail', args=['release-1.0']))
        before_time = self._get_last_modified_epoch(response)
        time.sleep(3)

        args = {"name": "Fedora", "short": "f", "version": '21', "release_type": "ga"}
        response = self.client.post(reverse('release-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(reverse('release-detail', args=['release-1.0']))
        after_time = self._get_last_modified_epoch(response)
        self.assertGreaterEqual(after_time - before_time, 3)

    def test_after_update_last_modified_time_should_change(self):
        response = self.client.get(reverse('release-list') + '?active=True')
        before_time = self._get_last_modified_epoch(response)
        time.sleep(2)

        args = {"active": False}
        response = self.client.patch(reverse('release-detail',
                                             kwargs={'release_id': 'release-1.0'}), args, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        url = reverse('release-list') + '?active=True'
        response = self.client.get(url)
        after_time = self._get_last_modified_epoch(response)
        self.assertGreaterEqual(after_time - before_time, 2)

        response = self.client.get(reverse('release-detail', args=['release-1.0']))
        before_time = self._get_last_modified_epoch(response)
        time.sleep(3)

        args = {"name": 'test_name'}
        response = self.client.patch(reverse('release-detail',
                                             kwargs={'release_id': 'release-1.0'}), args, format='json')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.client.get(reverse('release-detail', args=['release-1.0']))
        after_time = self._get_last_modified_epoch(response)
        self.assertGreaterEqual(after_time - before_time, 3)


class ProductLastModifiedResponseTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/release/fixtures/tests/base_product.json",
        "pdc/apps/release/fixtures/tests/product_version.json"
    ]

    def _get_last_modified_epoch(self, response):
        time_str = response.get('Last-Modified')
        temp_time = time.strptime(time_str, "%a, %d %b %Y %H:%M:%S %Z")
        return int(time.mktime(temp_time))

    def test_after_create_last_modified_time_should_change(self):
        response = self.client.get(reverse('product-list'))
        before_time = self._get_last_modified_epoch(response)
        time.sleep(2)

        args = {"name": "Fedora", "short": "f"}
        response = self.client.post(reverse('product-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(reverse('product-list'))
        after_time = self._get_last_modified_epoch(response)
        self.assertGreaterEqual(after_time - before_time, 2)

    def test_after_update_last_modified_time_should_change(self):
        response = self.client.get(reverse('product-list'))
        before_time = self._get_last_modified_epoch(response)
        time.sleep(2)

        self.client.patch(reverse('product-detail', args=['product']), {'name': 'changed_name'}, format='json')
        response = self.client.get(reverse('product-list'))
        after_time = self._get_last_modified_epoch(response)
        self.assertGreaterEqual(after_time - before_time, 2)

    def test_change_product_verion_modified_time_should_change(self):
        response = self.client.get(reverse('product-list'))
        before_time = self._get_last_modified_epoch(response)
        time.sleep(3)

        # add one to product's product version
        args = {"name": "Our Awesome Product", "short": "product",
                "version": "2", "product": "product"}
        response = self.client.post(reverse('productversion-list'), args)
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.get(reverse('product-list'))
        after_time = self._get_last_modified_epoch(response)
        self.assertGreaterEqual(after_time - before_time, 3)
