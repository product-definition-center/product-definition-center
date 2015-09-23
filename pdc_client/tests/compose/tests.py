# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc_client.test_helpers import CLITestCase
from pdc_client.runner import Runner


class ComposeTestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()
        self.compose_detail = {
            "compose_id": "awesome-product-20130203.7",
            "compose_date": "2013-02-03",
            "compose_type": "nightly",
            "compose_respin": 0,
            "release": "aifv-5802",
            "compose_label": "RC-3.0",
            "deleted": False,
            "rpm_mapping_template": "https://pdc.example.com/rest_api/v1/composes/awesome-product-20130203.7/rpm-mapping/{{package}}/",
            "sigkeys": [
                "fd431d51"
            ],
            "acceptance_testing": "untested",
            "linked_releases": [
                "sap-7.0-awesome-product"
            ],
            "rtt_tested_architectures": {
                "Workstation": {
                    "x86_64": "untested"
                }
            }
        }

    def test_list_multi_page(self, api):
        api.add_endpoint('composes', 'GET', [
            {'compose_id': 'awesome-product-20150924.{}'.format(x)}
            for x in range(23)
        ])
        with self.expect_output('list_multi_page.txt'):
            self.runner.run(['compose-list'])
        self.assertEqual(api.calls['composes'],
                         [('GET', {'page': 1, 'deleted': False}),
                          ('GET', {'page': 2, 'deleted': False})])

    def test_list_deleted(self, api):
        api.add_endpoint('composes', 'GET', [])
        with self.expect_output('empty.txt'):
            self.runner.run(['compose-list', '--deleted'])
        self.assertEqual(api.calls['composes'],
                         [('GET', {'page': 1, 'deleted': True})])

    def test_info(self, api):
        api.add_endpoint('composes/awesome-product-20130203.7', 'GET', self.compose_detail)
        with self.expect_output('info.txt'):
            self.runner.run(['compose-info', 'awesome-product-20130203.7'])
        self.assertDictEqual(api.calls,
                             {'composes/awesome-product-20130203.7': [('GET', {})]})

    def test_info_json(self, api):
        api.add_endpoint('composes/awesome-product-20130203.7', 'GET', self.compose_detail)
        with self.expect_output('info.json', parse_json=True):
            self.runner.run(['--json', 'compose-info', 'awesome-product-20130203.7'])
        self.assertDictEqual(api.calls,
                             {'composes/awesome-product-20130203.7': [('GET', {})]})

    def test_update(self, api):
        api.add_endpoint('composes/awesome-product-20130203.7', 'GET', self.compose_detail)
        with self.expect_output('info.txt'):
            self.runner.run(['compose-update', 'awesome-product-20130203.7',
                             '--acceptance-testing', 'passed',
                             '--linked-releases', 'sap-7.0-awesome-product',
                             '--rtt-tested-architectures', 'Workstation:x86_64:passed'
                             ])
        self.assertDictEqual(api.calls, {'composes/awesome-product-20130203.7':
                                         [('PATCH', {'acceptance_testing': 'passed',
                                                     'linked_releases': ['sap-7.0-awesome-product'],
                                                     'rtt_tested_architectures': {'Workstation': {'x86_64': 'passed'}}}),
                                          ('GET', {})]})

    def test_update_wrong_input1(self, api):
        with self.expect_failure():
            self.runner.run(['compose-update', 'awesome-product-20130203.7',
                             '--acceptance-testing', 'passed',
                             '--linked-releases', 'sap-7.0-awesome-product',
                             '--rtt-tested-architectures', 'Workstation:x86_64:passed:wronginput'
                             ])

    def test_update_wrong_input2(self, api):
        with self.expect_failure():
            self.runner.run(['compose-update', 'awesome-product-20130203.7',
                             '--acceptance-testing', 'wronginput',
                             '--linked-releases', 'sap-7.0-awesome-product',
                             '--rtt-tested-architectures', 'Workstation:x86_64:passed'
                             ])
