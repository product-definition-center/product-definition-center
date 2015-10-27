# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from pdc_client.plugin_helpers import PDCClientPlugin


class PermissionPlugin(PDCClientPlugin):
    def register(self):
        self.set_command('permission')

        list_parser = self.add_action('list', help='list my permissions')
        list_parser.set_defaults(func=self.permission_list)

    def permission_list(self, args):
        permissions = self.__get_permissions(self.client.auth['current-user'])
        if args.json:
            print json.dumps(permissions)
            return

        for permission in sorted(permissions):
            print permission

    def __get_permissions(self, res, **kwargs):
        """
        This call returns current login user's permissions.
        """
        response = res(**kwargs)
        return response.get('permissions', None)


PLUGIN_CLASSES = [PermissionPlugin]
