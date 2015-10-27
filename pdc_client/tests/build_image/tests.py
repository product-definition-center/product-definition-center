# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc_client.test_helpers import CLITestCase
from pdc_client.runner import Runner


class BuildImageTestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()

    def _setup_list_1(self, api):
        api.add_endpoint('build-images', 'GET', [
            {'image_id': 'build-image-{}'.format(x),
             'md5': '111122223333444455556666777788{:02}'.format(x)}
            for x in range(30)
        ])

    def _setup_detail(self, api):
        obj = {'image_id': 'test_image_1',
               'url': 'http://127.0.0.1:8000/rest_api/v1/build-images/1/',
               'image_format': 'docker',
               'md5': '11112222333344445555666677778899',
               'rpms': [],
               'archives': [],
               'releases': []}
        api.add_endpoint('build-images/1', 'PATCH', obj)
        api.add_endpoint('build-images/1', 'GET', obj)
        api.add_endpoint('build-images', 'POST', obj)

    def _setup_list_2(self, api):
        filter_result = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "archives": [],
                    "image_format": "docker",
                    "image_id": "test_image_1",
                    "md5": "11112222333344445555666677778899",
                    "releases": [],
                    "rpms": [],
                    "url": "http://127.0.0.1:8000/rest_api/v1/build-images/1/"
                }
            ]
        }

        api.add_endpoint('build-images', 'GET', filter_result)

    def test_list(self, api):
        self._setup_list_1(api)
        with self.expect_output('list_multi_page.txt'):
            self.runner.run(['build-image', 'list'])
        self.assertEqual(api.calls['build-images'],
                         [('GET', {'page': 1}),
                          ('GET', {'page': 2})])

    def test_info(self, api):
        self._setup_detail(api)
        self._setup_list_2(api)
        with self.expect_output('detail.json', parse_json=True):
            self.runner.run(['--json', 'build-image', 'info', 'test_image_1'])
        self.assertEqual(api.calls['build-images'], [('GET', {'image_id': 'test_image_1'})])
