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

rpms_json_path = os.path.join(os.path.dirname(__file__), "test_tree.json")
rpms_json = open(rpms_json_path, "r").read()


class TreeAPITestCase(APITestCase):
    def test_create_unreleasedvariant(self):
        url = reverse('unreleasedvariant-list')
        data = {
            'variant_id': "core", 'variant_uid': "Core",
            'variant_name': "Core", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-core-0-1", 'modulemd': 'foobar'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_tree(self):
        url = reverse('unreleasedvariant-list')
        data = {
            'variant_id': "shells", 'variant_uid': "Shells",
            'variant_name': "Shells", 'variant_version': "0",
            'variant_release': "1", 'variant_type': 'module',
            'koji_tag': "module-shells-0-1", 'modulemd': 'foobar'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url = reverse('tree-list')
        data = {
            'tree_id': "Shells-x86_64-20160529.0", 'tree_date': "2016-05-29",
            'variant': {
                'variant_uid': "Shells",
                'variant_version': "0",
                'variant_release': "1"
            },
            'arch': "x86_64", 'content_format': ['rpm'],
            'content': {'rpm': json.dumps(json.loads(rpms_json))},
            'url': "/mnt/test/location"}
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
