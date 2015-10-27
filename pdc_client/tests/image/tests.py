# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from pdc_client.test_helpers import CLITestCase
from pdc_client.runner import Runner


class ImageTestCase(CLITestCase):
    def setUp(self):
        self.runner = Runner()
        self.runner.setup()

    def _setup_list(self, api):
        api.add_endpoint('images', 'GET', [
            {'file_name': 'image-{}'.format(x),
             'sha256': '112233445566778899{:02}'.format(x)}
            for x in range(30)
        ])

    def _setup_detail(self, api):
        api.add_endpoint('images', 'GET', [
            {'file_name': 'unique_image.iso',
             'mtime': 1442923687,
             'image_type': 'dvd',
             'image_format': 'iso',
             'arch': 'x86_64',
             'disc_number': 1,
             'disc_count': 1,
             'size': 123456789,
             'bootable': True,
             'volume_id': 'VolumeID',
             'md5': '11111111111111111111111111111111',
             'sha1': '2222222222222222222222222222222222222222',
             'sha256': '3333333333333333333333333333333333333333333333333333333333333333',
             'implant_md5': '00000000000000000000000000000000',
             'composes': ['compose-1']}])

    def _setup_duplicit_detail(self, api):
        api.add_endpoint('images', 'GET', [
            {'file_name': 'unique_image.iso',
             'mtime': 1442923687,
             'image_type': 'dvd',
             'image_format': 'iso',
             'arch': 'x86_64',
             'disc_number': 1,
             'disc_count': 1,
             'size': 123456789,
             'bootable': True,
             'volume_id': 'VolumeID',
             'md5': '11111111111111111111111111111111',
             'sha1': '2222222222222222222222222222222222222222',
             'sha256': '3333333333333333333333333333333333333333333333333333333333333333',
             'implant_md5': '00000000000000000000000000000000',
             'composes': ['compose-1']},
            {'file_name': 'unique_image.iso',
             'mtime': 1442923687,
             'image_type': 'dvd',
             'image_format': 'iso',
             'arch': 'x86_64',
             'disc_number': 1,
             'disc_count': 1,
             'size': 123456789,
             'bootable': True,
             'volume_id': 'VolumeID',
             'md5': '11111111111111111111111111111111',
             'sha1': '2222222222222222222222222222222222222222',
             'sha256': '4444444444444444444444444444444444444444444444444444444444444444',
             'implant_md5': '00000000000000000000000000000000',
             'composes': ['compose-1']}])

    def test_list(self, api):
        self._setup_list(api)
        with self.expect_output('list_multi_page.txt'):
            self.runner.run(['image', 'list'])
        self.assertEqual(api.calls['images'],
                         [('GET', {'page': 1}),
                          ('GET', {'page': 2})])

    def test_list_json(self, api):
        self._setup_list(api)
        with self.expect_output('list_multi_page.json', parse_json=True):
            self.runner.run(['--json', 'image', 'list'])
        self.assertEqual(api.calls['images'],
                         [('GET', {'page': 1}),
                          ('GET', {'page': 2})])

    def test_list_filters(self, api):
        api.add_endpoint('images', 'GET', [])
        filters = ['sha256', 'compose', 'volume-id', 'sha1', 'image-type',
                   'file-name', 'image-format', 'arch', 'md5', 'implant-md5']
        for filter in filters:
            with self.expect_output('empty.txt'):
                self.runner.run(['image', 'list', '--' + filter, filter])
        self.assertEqual(api.calls['images'],
                         [('GET', {'page': 1, filter.replace('-', '_'): filter})
                          for filter in filters])

    def test_show_sha256(self, api):
        self._setup_list(api)
        with self.expect_output('list_multi_page_with_sha256.txt'):
            self.runner.run(['image', 'list', '--show-sha256'])
        self.assertEqual(api.calls['images'],
                         [('GET', {'page': 1}),
                          ('GET', {'page': 2})])

    def test_info(self, api):
        self._setup_detail(api)
        with self.expect_output('info.txt'):
            self.runner.run(['image', 'info', 'unique_filename.iso'])
        self.assertEqual(api.calls['images'],
                         [('GET', {'file_name': 'unique_filename.iso'})])

    def test_info_json(self, api):
        self._setup_detail(api)
        with self.expect_output('info.json', parse_json=True):
            self.runner.run(['--json', 'image', 'info', 'unique_filename.iso'])
        self.assertEqual(api.calls['images'],
                         [('GET', {'file_name': 'unique_filename.iso'})])

    def test_info_ambiguous(self, api):
        self._setup_duplicit_detail(api)
        with self.expect_output('duplicit.txt'):
            with self.expect_failure():
                self.runner.run(['image', 'info', 'unique_filename.iso'])
        self.assertEqual(api.calls['images'],
                         [('GET', {'file_name': 'unique_filename.iso'})])

    def test_info_with_sha(self, api):
        self._setup_detail(api)
        with self.expect_output('info.txt'):
            self.runner.run(['image', 'info', 'unique_filename.iso',
                             '--sha256', '3333333333333333333333333333333333333333333333333333333333333333'])
        self.assertEqual(api.calls['images'],
                         [('GET', {'file_name': 'unique_filename.iso',
                                   'sha256': '3333333333333333333333333333333333333333333333333333333333333333'})])
