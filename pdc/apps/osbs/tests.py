#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.urlresolvers import reverse
from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin

from . import models
from pdc.apps.component import models as component_models


class OSBSRESTTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        'pdc/apps/release/fixtures/tests/release.json',
        'pdc/apps/component/fixtures/tests/upstream.json',
        'pdc/apps/component/fixtures/tests/global_component.json',
        'pdc/apps/osbs/fixtures/tests/records.json',
    ]

    @classmethod
    def setUpTestData(cls):
        type = component_models.ReleaseComponentType.objects.get(name='container')
        type.has_osbs = True
        type.save()

    def test_create_component_creates_osbs(self):
        response = self.client.post(reverse('releasecomponent-list'),
                                    {'name': 'test', 'release': 'release-1.0',
                                     'global_component': 'python', 'type': 'container'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Two already existed in fixtures.
        self.assertEqual(3, models.OSBSRecord.objects.count())

    def test_create_component_with_bad_type_does_not_create_osbs(self):
        response = self.client.post(reverse('releasecomponent-list'),
                                    {'name': 'test', 'release': 'release-1.0',
                                     'global_component': 'python', 'type': 'rpm'},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(2, models.OSBSRecord.objects.count())

    def test_update_component_to_different_type_deletes_osbs(self):
        response = self.client.patch(reverse('releasecomponent-detail', args=[1]),
                                     {'type': 'rpm'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(1, models.OSBSRecord.objects.count())

    def test_change_type_creates_osbs(self):
        type = component_models.ReleaseComponentType.objects.get(name='rpm')
        type.has_osbs = True
        type.save()
        self.assertEqual(3, models.OSBSRecord.objects.count())

    def test_change_type_deletes_osbs(self):
        type = component_models.ReleaseComponentType.objects.get(name='container')
        type.has_osbs = False
        type.save()
        self.assertEqual(0, models.OSBSRecord.objects.count())

    def test_list_osbs(self):
        response = self.client.get(reverse('osbs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filter_by_release(self):
        response = self.client.get(reverse('osbs-list'), {'release': 'release-2.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_by_component_name(self):
        response = self.client.get(reverse('osbs-list'), {'component_name': 'bash'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_filter_by_autorebuild(self):
        response = self.client.get(reverse('osbs-list'), {'autorebuild': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_osbs(self):
        response = self.client.get(reverse('osbs-detail', args=['release-1.0/python27']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         {'component': {'id': 1,
                                        'name': 'python27',
                                        'release': 'release-1.0'},
                          'autorebuild': True})

    def test_deleting_osbs_fails(self):
        response = self.client.delete(reverse('osbs-detail', args=['release-1.0/python27']))
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(2, models.OSBSRecord.objects.count())

    def test_update(self):
        response = self.client.put(reverse('osbs-detail', args=['release-1.0/python27']),
                                   {'autorebuild': False},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['autorebuild'])
        self.assertNumChanges([1])
        r = models.OSBSRecord.objects.get(component_id=1)
        self.assertFalse(r.autorebuild)

    def test_partial_update(self):
        response = self.client.patch(reverse('osbs-detail', args=['release-1.0/python27']),
                                     {'autorebuild': False},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['autorebuild'])
        self.assertNumChanges([1])
        r = models.OSBSRecord.objects.get(component_id=1)
        self.assertFalse(r.autorebuild)

    def test_can_unset_autorebuild(self):
        response = self.client.patch(reverse('osbs-detail', args=['release-1.0/python27']),
                                     {'autorebuild': None},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['autorebuild'])
        self.assertNumChanges([1])
        r = models.OSBSRecord.objects.get(component_id=1)
        self.assertIsNone(r.autorebuild)

    def test_cloning_release_clones_osbs(self):
        self.client.post(reverse('releaseclone-list'),
                         {'old_release_id': 'release-1.0', 'version': '1.1'},
                         format='json')
        records = models.OSBSRecord.objects.filter(component__release__release_id='release-1.1')
        self.assertEqual(2, len(records))
        self.assertTrue(records.get(component__name='python27').autorebuild)
        self.assertFalse(records.get(component__name='MySQL-python').autorebuild)
        self.assertNumChanges([6])  # 1 release, 3 components, 2 osbs records

    def test_update_with_wrong_key(self):
        response = self.client.put(reverse('osbs-detail', args=['release-1.0/python27']),
                                   {'autorebuild': False, 'wrongkey': True},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": 'Unknown fields: "wrongkey".'})

    def test_partial_update_with_wrong_key(self):
        response = self.client.patch(reverse('osbs-detail', args=['release-1.0/python27']),
                                     {'wrongkey': False},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": 'Unknown fields: "wrongkey".'})
