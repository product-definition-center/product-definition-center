# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import sys

from pdc_client import get_paged
from pdc_client.plugin_helpers import PDCClientPlugin, add_parser_arguments, extract_arguments


class BuildImagePlugin(PDCClientPlugin):
    def register(self):
        subcmd = self.add_command('build-image-list', help='list all build images')
        subcmd.add_argument('--show-md5', action='store_true',
                            help='whether to display md5 checksums')
        add_parser_arguments(subcmd, {'component_name': {},
                                      'rpm_version': {},
                                      'rpm_release': {},
                                      'image_id': {},
                                      'image_format': {},
                                      'md5': {},
                                      'archive_build_nvr': {},
                                      'archive_name': {},
                                      'archive_size': {},
                                      'archive_md5': {},
                                      'release_id': {}},
                             group='Filtering')

        subcmd.set_defaults(func=self.list_build_image)

        subcmd = self.add_command('build-image-info', help='display details of a build image')
        subcmd.add_argument('image_id', metavar='IMAGE_ID')
        subcmd.set_defaults(func=self.build_image_info)

    def _print_build_image_list(self, build_images, with_md5=False):
        fmt = '{image_id}'
        if with_md5:
            fmt += ' {md5}'
        for build_image in build_images:
            print fmt.format(**build_image)

    def list_build_image(self, args):
        filters = extract_arguments(args)
        build_images = get_paged(self.client['build-images']._, **filters)
        if args.json:
            print json.dumps(list(build_images))
            return
        self._print_build_image_list(build_images, args.show_md5)

    def build_image_info(self, args, image_id=None):
        image_id = image_id or args.image_id
        build_images = self.client['build-images']._(image_id=image_id)
        if not build_images['count']:
            print 'Not found'
            sys.exit(1)
        build_image = build_images['results'][0]
        if args.json:
            print json.dumps(build_image)
            return
        fmt = '{:20} {}'
        print fmt.format('Image ID', build_image['image_id'])
        print fmt.format('Image Format', build_image['image_format'])
        print fmt.format('URL', build_image['url'])
        print fmt.format('MD5', build_image['md5'])

        for key in ('releases', 'rpms'):
            if build_image[key]:
                print '\nRelated %s:' % key
                for value in build_image[key]:
                    print ' * {}'.format(value)

        if build_image['archives']:
            print '\nRelated archives:'
            fmt = '* {:40}{:60}{}'
            print fmt.format('MD5', 'Name', 'Build NVR')
            fmt = '  {:40}{:60}{}'
            for archive in build_image['archives']:
                print fmt.format(archive['md5'], archive['name'], archive['build_nvr'])


PLUGIN_CLASSES = [BuildImagePlugin]
