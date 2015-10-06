# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from pdc_client import get_paged
from pdc_client.plugin_helpers import PDCClientPlugin, add_parser_arguments, extract_arguments


class ReleasePlugin(PDCClientPlugin):
    def register(self):
        subcmd = self.add_command('release-list', help='list all releases')
        subcmd.add_argument('--inactive', action='store_true',
                            help='show only inactive releases')
        subcmd.add_argument('--all', action='store_true',
                            help='show both active and inactive releases')
        subcmd.set_defaults(func=self.list_releases)

        subcmd = self.add_command('release-info', help='display details of a release')
        subcmd.add_argument('release_id', metavar='RELEASE_ID')
        subcmd.set_defaults(func=self.release_info)

        subcmd = self.add_admin_command('release-update',
                                        help='update an existing release')
        subcmd.add_argument('release_id', metavar='RELEASE_ID')
        self.add_release_arguments(subcmd)
        subcmd.set_defaults(func=self.release_update)

        subcmd = self.add_admin_command('release-create',
                                        help='create new release')
        self.add_release_arguments(subcmd)
        subcmd.set_defaults(func=self.release_create)

    def add_release_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--activate', action='store_const', const=True, dest='active')
        group.add_argument('--deactivate', action='store_const', const=False, dest='active')
        add_parser_arguments(parser, {
            'version': {},
            'short': {},
            'release_type': {},
            'product_version': {},
            'name': {},
            'base_product': {},
            'bugzilla__product': {'arg': 'bugzilla-product'},
            'dist_git__branch': {'arg': 'dist-git-branch'}})

        self.run_hook('release_parser_setup', parser)

    def list_releases(self, args):
        filters = {}
        if args.inactive:
            filters['active'] = False
        elif not args.all:
            filters['active'] = True

        releases = get_paged(self.client.releases._, **filters)
        if args.json:
            print json.dumps(list(releases))
            return

        fmt = '{:25} {:35} {}'
        for release in releases:
            print fmt.format(release['release_id'], release['name'],
                             'active' if release['active'] else 'inactive')

    def release_info(self, args, release_id=None):
        release_id = release_id or args.release_id
        release = self.client.releases[release_id]._()
        variants = get_paged(self.client['release-variants']._, release=release_id)
        if args.json:
            release['variants'] = list(variants)
            print json.dumps(release)
            return

        fmt = '{:20} {}'
        print fmt.format('Release ID', release['release_id'])
        print fmt.format('Name', release['name'])
        print fmt.format('Short Name', release['short'])
        print fmt.format('Version', release['version'])
        print fmt.format('Type', release['release_type'])
        print fmt.format('Product Version', release['product_version'] or '')
        print fmt.format('Base Product', release['base_product'] or '')
        print fmt.format('Activity', 'active' if release['active'] else 'inactive')
        print fmt.format('Integrated With', release['integrated_with'] or '')

        # Call plugins
        self.run_hook('release_info', release)

        if release['bugzilla']:
            print '\nBugzilla'
            print fmt.format('Product', release['bugzilla']['product'])

        if release['dist_git']:
            print '\nDist Git'
            print fmt.format('Branch', release['dist_git']['branch'])

        print '\nVariants'
        fmt = '{:25} {:20} {:20} {:15} {}'
        print fmt.format('UID', 'ID', 'Name', 'Type', 'Arches')
        for variant in variants:
            print fmt.format(variant['uid'], variant['id'], variant['name'],
                             variant['type'], ', '.join(variant['arches']))

    def release_update(self, args):
        data = self.get_release_data(args)

        if data:
            self.logger.debug('Updating release {} with data {}'.format(args.release_id, data))
            self.client.releases[args.release_id]._ += data
        else:
            self.logger.info('No change required, not making a request')

        self.release_info(args)

    def release_create(self, args):
        data = self.get_release_data(args)
        self.logger.debug('Creating release with data {}'.format(data))
        response = self.client.releases._(data)
        self.release_info(args, response['release_id'])

    def get_release_data(self, args):
        data = extract_arguments(args)
        if args.active is not None:
            data['active'] = args.active

        self.run_hook('release_update_prepare', args, data)

        return data


PLUGIN_CLASSES = [ReleasePlugin]
