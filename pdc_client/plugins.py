# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

#
# To implement a plugin, a subclass of PDCClientPlugin must be provided in a
# file in any of PLUGIN_DIRS. The file with the plugin must also define a top
# level constant PLUGIN_CLASSES. The value of this constant should be a list of
# PDCClientPlugin subclasses defined in this module. It is therefore possible
# to define multiple plugins in a single file.
#
# Each plugin must define `register` method. It is used to register command
# line arguments and subcommands. There are helper methods `add_command` and
# `add_admin_command`. The plugin can also these predefined properties:
#   * logger - this logger inherits settings from the client
#   * client - instance of PDClient connected to a server
#
# It can also use these methods:
#   * run_hook - to invoke code from other plugins (see below for details)
#
# The alternative way to use plugins is to define hooks that can be invoked
# from elsewhere. These hooks are invoked using the run_hook method. Its first
# argument is the name of the hook. All other arguments and keyword arguments
# will be passed to the hook.
#
# The implementation of the hook should be a top level function with the same
# name as used when invoking the hook. Its return value is ignored.
#
# The base client does not define and use any hooks.
#

import logging
import itertools
import sys


DATA_PREFIX = 'data__'


class PDCClientPlugin(object):
    """
    Abstract base class for plugins providing their own commands. Each subclass
    must implement `register` methods.
    """
    def __init__(self, runner):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.runner = runner
        self.help_all = '--help-all' in sys.argv

    @property
    def client(self):
        return self.runner.client

    def run_hook(self, hook, *args, **kwargs):
        self.runner.run_hook(hook, *args, **kwargs)

    def _before_register(self, parser):
        self.parser = parser

    def register(self):
        raise NotImplementedError('Plugin must implement `register` method.')

    def add_command(self, *args, **kwargs):
        """Define new subcommand.

        For accepted arguments, see `argparse.ArgumentParser.add_argument`.
        """
        return self.parser.add_parser(*args, **kwargs)

    def add_admin_command(self, *args, **kwargs):
        """Define new admin subcommand.

        Help of this subcommand will be hidden for regular --help option, but
        will show when --help-all is used. Otherwise identical to add_command.
        """
        if not self.help_all:
            kwargs.pop('help', None)
        return self.parser.add_parser(*args, **kwargs)


def get_paged(res, **kwargs):
    """
    This call is equivalent to `res(**kwargs)`, only it retrieves all pages and
    returns the results joined into a single iterable. The advantage over
    retrieving everything at once is that the result can be consumed
    immediately.
    """
    def worker():
        kwargs['page'] = 1
        while True:
            response = res(**kwargs)
            yield response['results']
            if response['next']:
                kwargs['page'] += 1
            else:
                break
    return itertools.chain.from_iterable(worker())


def add_parser_arguments(parser, args, group=None, prefix=DATA_PREFIX):
    """
    Helper method that populates parser arguments. The argument values can
    be later retrieved with `extract_arguments` method.

    The `args` argument to this method should be a dict with strings as
    keys and dicts as values. The keys will be used as keys in returned
    data. Their values will be passed as kwargs to `parser.add_argument`.
    There is special value `arg` that will be used as argument name if
    present, otherwise a name will be generated based on the key.

    If `group` is a string, it will be used as group header in help output.
    """
    if group:
        parser = parser.add_argument_group(group)
    for arg, kwargs in args.iteritems():
        arg_name = kwargs.pop('arg', arg.replace('_', '-'))
        if 'metavar' not in kwargs:
            kwargs['metavar'] = arg.upper()
        parser.add_argument('--' + arg_name, dest=prefix + arg, **kwargs)


def extract_arguments(args, prefix=DATA_PREFIX):
    """
    Return a dict of arguments created by `add_parser_arguments`.
    """
    data = {}
    for key, value in args.__dict__.iteritems():
        if key.startswith(prefix) and value is not None:
            parts = key[len(prefix):].split('__')
            d = data
            for p in parts[:-1]:
                d[p] = {}
                d = d[p]
            d[parts[-1]] = value if value != '' else None
    return data
