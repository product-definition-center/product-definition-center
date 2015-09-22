# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json
import sys
from datetime import datetime

from pdc_client.plugin_helpers import PDCClientPlugin, get_paged, add_parser_arguments, extract_arguments


info_desc = """Generally there may be duplicate file names. If the file name
you provide matches more that image, you will get a list of all those images
together with their SHA256 checksums. You desambiguate by providing the
checksum as a command line argument.
"""


def size_format(num):
    fmt = '{:.1f} {}B'
    factor = 1024.0
    for unit in ('', 'Ki', 'Mi', 'Gi'):
        if num < factor:
            return fmt.format(num, unit)
        num /= factor
    return fmt.format(num, 'Ti')


class ImagePlugin(PDCClientPlugin):
    def register(self):
        subcmd = self.add_command('image-list', help='list all images')
        subcmd.add_argument('--show-sha256', action='store_true',
                            help='whether to display SHA256 checksums along with the file names')
        add_parser_arguments(subcmd, {'arch': {},
                                      'compose': {},
                                      'file_name': {},
                                      'image_format': {},
                                      'image_type': {},
                                      'implant_md5': {},
                                      'md5': {},
                                      'sha1': {},
                                      'sha256': {},
                                      'volume_id': {}},
                             group='Filtering')
        subcmd.set_defaults(func=self.image_list)

        subcmd = self.add_command('image-info', help='display details of an image',
                                  description=info_desc)
        subcmd.add_argument('filename', metavar='FILENAME')
        subcmd.add_argument('--sha256', nargs='?')
        subcmd.set_defaults(func=self.image_info)

    def _print_image_list(self, images, with_sha=False):
        fmt = '{file_name}'
        if with_sha:
            fmt += ' {sha256}'
        for image in images:
            print fmt.format(**image)

    def image_list(self, args):
        filters = extract_arguments(args)
        images = get_paged(self.client.images._, **filters)
        if args.json:
            print json.dumps(list(images))
            return

        self._print_image_list(images, args.show_sha256)

    def image_info(self, args):
        filters = {'file_name': args.filename}
        if args.sha256:
            filters['sha256'] = args.sha256
        image = self.client.images._(**filters)
        if image['count'] == 0:
            print 'Not found'
            sys.exit(1)
        elif image['count'] > 1:
            print 'More than one image with that name, use --sha256 to specify.'
            self._print_image_list(image['results'], True)
            sys.exit(1)
        else:
            image = image['results'][0]
            if args.json:
                print json.dumps(image)
                return

            mtime = datetime.utcfromtimestamp(image['mtime'])

            fmt = '{:15} {}'
            print fmt.format('File Name', image['file_name'])
            print fmt.format('Image Type', image['image_type'])
            print fmt.format('Image Format', image['image_format'])
            print fmt.format('Arch', image['arch'])
            print fmt.format('Disc', '{} / {}'.format(image['disc_number'], image['disc_count']))
            print fmt.format('Modified', '{} ({})'.format(image['mtime'], mtime))
            print fmt.format('Size', '{} ({})'.format(image['size'], size_format(image['size'])))
            print fmt.format('Bootable', 'yes' if image['bootable'] else 'no')
            print fmt.format('Volume ID', image['volume_id'])
            print fmt.format('Implant MD5', image['implant_md5'])

            print '\nChecksums:'
            print ' {:7} {}'.format('MD5', image['md5'])
            print ' {:7} {}'.format('SHA1', image['sha1'])
            print ' {:7} {}'.format('SHA256', image['sha256'])

            if image['composes']:
                print '\nUsed in composes:'
                for compose in image['composes']:
                    print ' * {}'.format(compose)

PLUGIN_CLASSES = [ImagePlugin]
