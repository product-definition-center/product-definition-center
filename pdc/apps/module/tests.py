# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import os.path

from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from pdc.apps.common.test_utils import TestCaseWithChangeSetMixin


class ModuleAPITestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        'pdc/apps/module/fixtures/test/rpm.json',
    ]

    def test_create_unreleasedvariant1(self):
        url = reverse('unreleasedvariant-list')
        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core-0-1", 'modulemd': 'foobar'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_unreleasedvariant2(self):
        url = reverse('unreleasedvariant-list')
        data = {
            'variant_id': "shells", 'variant_uid': "Shells",
            'variant_name': "Shells", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-shells-0-1", 'modulemd': 'foobar'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_two_variants_query_by_active(self):
        url = reverse('unreleasedvariant-list')
        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core-0-1", 'modulemd': 'foobar',
            'active': False,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "2", 'variant_type': 'module',
            'koji_tag': "module-core-0-2", 'modulemd': 'foobar',
            'active': True,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = {'active': True}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)
        self.assertEqual(results['results'][0]['koji_tag'], 'module-core-0-2')

    def test_filter_build_deps(self):
        url = reverse('unreleasedvariant-list')

        # Add variant with 'base-runtime-master' build-dep.
        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core-0-1", 'modulemd': 'foobar',
            'build_deps': [{'dependency':'base-runtime', 'stream': 'master'}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Add variant with 'base-runtime-f26' build-dep.
        data = {
            'variant_id': "core3", 'variant_uid': "Core3",
            'variant_name': "Core3", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core3-0-1", 'modulemd': 'foobar',
            'build_deps': [{'dependency':'base-runtime', 'stream': 'f26'}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Add variant with 'bootstrap-master' build-dep.
        data = {
            'variant_id': "core2", 'variant_uid': "Core2",
            'variant_name': "Core2", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core2-0-1", 'modulemd': 'foobar',
            'build_deps': [{'dependency':'bootstrap', 'stream': 'master'}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Try to get unknown build-dep
        data = {'build_dep_name': "unknown"}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Try to get base-runtime build-dep
        data = {'build_dep_name': "base-runtime"}
        response = self.client.get(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # Try to get base-runtime-master build-dep
        data = {'build_dep_name': "base-runtime",
                'build_dep_stream': "master"}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]["variant_uid"], "Core")

    def test_create_with_new_rpms(self):
        url = reverse('unreleasedvariant-list')
        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core-0-1", 'modulemd': 'foobar',
            'active': False,
            'rpms': [{'name': 'new_rpm', 'epoch': 0, 'version': '1.0.0',
                        'release': '1', 'arch': 'src', 'srpm_name': 'new_srpm'}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([2])
        self.assertIn('new_rpm', response.content)

    def test_filter_by_rpms(self):
        url = reverse('unreleasedvariant-list')
        # add a variant with rpm 'foobar' from branch 'master'
        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core-0-1", 'modulemd': 'foobar',
            'active': True,
            'rpms': [{'name': 'foobar', 'epoch': 0, 'version': '1.0.0',
                      'release': '1', 'arch': 'src', 'srpm_name': 'foobar',
                      'srpm_commit_branch': 'master'}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('foobar', response.content)

        # add another variant with rpm 'foobar' from branch 'rawhide'
        data = {
            'variant_id': "core2", 'variant_uid': "Core2",
            'variant_name': "Core2", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core2-0-1", 'modulemd': 'foobar',
            'active': True,
            'rpms': [{'name': 'foobar', 'epoch': 0, 'version': '2.0.0',
                      'release': '1', 'arch': 'src', 'srpm_name': 'foobar',
                      'srpm_commit_branch': 'rawhide'}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('foobar', response.content)

        # query modules with rpm name
        data = {'component_name': 'foobar'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertIn("Core", [x['variant_uid'] for x in response.data['results']])
        self.assertIn("Core2", [x['variant_uid'] for x in response.data['results']])

        # query modules with rpm name and branch
        data = {'component_name': 'foobar', 'component_branch': 'master'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertIn("Core", [x['variant_uid'] for x in response.data['results']])
        self.assertNotIn("Core2", [x['variant_uid'] for x in response.data['results']])

        data = {'component_name': 'foobar', 'component_branch': 'rawhide'}
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertNotIn("Core", [x['variant_uid'] for x in response.data['results']])
        self.assertIn("Core2", [x['variant_uid'] for x in response.data['results']])

    def test_create_with_exist_rpms(self):
        url = reverse('unreleasedvariant-list')
        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core-0-1", 'modulemd': 'foobar',
            'active': False,
            'rpms': [{
                "name": "bash-doc",
                "epoch": 0,
                "version": "1.2.3",
                "release": "4.b2",
                "arch": "x86_64",
                "srpm_name": "bash",
                "srpm_nevra": "bash-0:1.2.3-4.b2.src"}]
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNumChanges([1])
        self.assertIn('bash-doc', response.content)

        # Try to get the module with component "bash".
        response = self.client.get(url + '?component_name=bash', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 1)
        self.assertEqual(response.data['results'][0]["variant_uid"], "Core")

        # Try to get a module with unknown component.
        response = self.client.get(url + '?component_name=unknown', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('count'), 0)
