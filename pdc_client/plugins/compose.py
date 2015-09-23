# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from pdc_client import get_paged
from pdc_client.plugin_helpers import PDCClientPlugin, add_parser_arguments, extract_arguments


class ComposePlugin(PDCClientPlugin):
    def register(self):
        subcmd = self.add_command('compose-list', help='list all composes')
        subcmd.add_argument('--deleted', action='store_true',
                            help='show deleted composes')
        subcmd.set_defaults(func=self.list_composes)

        subcmd = self.add_command('compose-info', help='display details of a compose')
        subcmd.add_argument('compose_id', metavar='COMPOSE_ID')
        subcmd.set_defaults(func=self.compose_info)

        subcmd = self.add_admin_command('compose-update',
                                        help='partial update an existing compose.',
                                        description='only some compose fields can be modified by this call.\
                                                    these are acceptance_testing, linked_releases and rtt_tested_architectures.')
        subcmd.add_argument('compose_id', metavar='COMPOSE_ID')
        self.add_compose_arguments(subcmd)
        subcmd.set_defaults(func=self.compose_update)
        self.compose_update = subcmd

    def add_compose_arguments(self, parser):
        add_parser_arguments(parser, {
            'acceptance_testing': {'choices': ['passed', 'failed', 'untested']},
            'linked_releases': {'nargs': '*', 'metavar': 'RELEASE_ID'},
            'rtt_tested_architectures': {'nargs': '*', 'default': [], 'help': 'input format VARIANT:ARCHES:TESTING_STATUS'}})

    def list_composes(self, args):
        filters = {}
        if not args.deleted:
            filters['deleted'] = False
        else:
            filters['deleted'] = args.deleted

        composes = get_paged(self.client.composes._, **filters)
        if args.json:
            print json.dumps(list(composes))
            return

        for compose in composes:
            print compose['compose_id']

    def compose_info(self, args, compose_id=None):
        compose_id = compose_id or args.compose_id
        compose = self.client.composes[compose_id]._()
        if args.json:
            print json.dumps(compose)
            return

        fmt = '{:25} {}'
        print fmt.format('Compose ID', compose['compose_id'])
        print fmt.format('Compose Label', compose['compose_label'] or '')
        print fmt.format('Compose Date', compose['compose_date'])
        print fmt.format('Compose Respin', compose['compose_respin'])
        print fmt.format('Compose Type', compose['compose_type'])
        print fmt. format('Acceptance Testing', compose['acceptance_testing'])
        print fmt.format('Deleted', compose['deleted'])
        print fmt.format('Release', compose['release'])
        print fmt.format('Rpm Mapping Template', compose['rpm_mapping_template'])

        if compose['linked_releases']:
            print '\nLinked Releases'
            for release in compose['linked_releases']:
                print fmt.format('Release', release)

        if compose['sigkeys']:
            print '\nSigkeys'
            for sigkey in compose['sigkeys']:
                print fmt.format('Sigkey', sigkey)

        if compose['rtt_tested_architectures']:
            print '\nRtt Tested Architectures'
            fmt = '{:25} {:15} {}'
            print fmt.format('Variant', 'Arches', 'Testing Status')
            for key, value in compose['rtt_tested_architectures'].iteritems():
                for subkey, subvalue in value.iteritems():
                    print fmt.format(key, subkey, subvalue)

    def compose_update(self, args):
        data = self.get_compose_data(args)

        if data:
            self.logger.debug('Updating compose {} with data {}'.format(args.compose_id, data))
            self.client.composes[args.compose_id]._ += data
        else:
            self.logger.info('No change required, not making a request')

        self.compose_info(args)

    def get_compose_data(self, args):
        data = extract_arguments(args)
        rtts = data.get('rtt_tested_architectures', None)
        rtts = rtts if type(rtts) is list else [rtts]
        dic = {}
        for rtt in rtts:
            parts = rtt.split(':')
            if not len(parts) == 3:
                self.compose_update.error('Please input rtt-tested-architectures in format VARIANT:ARCHES:TESTING_STATUS.\n')

            variant = parts[0]
            arches = parts[1]
            status = parts[2]
            dic.update({variant: {arches: status}})

        data['rtt_tested_architectures'] = dic

        return data

PLUGIN_CLASSES = [ComposePlugin]
