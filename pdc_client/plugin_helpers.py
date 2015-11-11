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


DATA_PREFIX = 'data__'


class PDCClientPlugin(object):
    """
    Abstract base class for plugins providing their own commands. Each subclass
    must implement `register` methods.
    """
    def __init__(self, runner):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.runner = runner

    @property
    def client(self):
        return self.runner.client

    def run_hook(self, hook, *args, **kwargs):
        self.runner.run_hook(hook, *args, **kwargs)

    def _before_register(self, parser):
        self.parser = parser

    def register(self):
        raise NotImplementedError('Plugin must implement `register` method.')

    def set_command(self, *args, **kwargs):
        """Define new command.

        For accepted arguments, see `argparse.ArgumentParser.add_argument`.
        """
        if 'help' not in kwargs:
            kwargs['help'] = ''
        cmd = self.parser.add_parser(*args, **kwargs)
        self.subparsers = cmd.add_subparsers(metavar='ACTION')

    def add_action(self, *args, **kwargs):
        return self.subparsers.add_parser(*args, **kwargs)


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


def add_mutually_exclusive_args(parser, args, required=False, prefix=DATA_PREFIX):
    """
    Helper method that populates mutually exclusive arguments. The argument values can
    be later retrieved with `extract_arguments` method.

    The `args` argument to this method should be a dict with strings as
    keys and dicts as values. The keys will be used as keys in returned
    data. Their values will be passed as kwargs to `parser.add_argument`.
    There is special value `arg` that will be used as argument name if
    present, otherwise a name will be generated based on the key.

    ``required`` will be passed to `parser.add_mutually_exclusive_group` to
    to indicate that at least one of the mutually exclusive arguments is required.
    """
    parser = parser.add_mutually_exclusive_group(required=required)
    for arg, kwargs in args.iteritems():
        arg_name = kwargs.pop('arg', arg.replace('_', '-'))
        if 'metavar' not in kwargs:
            kwargs['metavar'] = arg.upper()
        parser.add_argument('--' + arg_name, dest=prefix + arg, **kwargs)


def add_create_update_args(parser, required_args, optional_args, create=False):
    """Wrapper around ``add_parser_arguments``.

    If ``create`` is True, one argument group will be created for each of
    ``required_args`` and ``optional_args``. Each required argument will have
    the ``required`` parameter set to True automatically.

    If ``create`` is False, only one group of optional arguments will be
    created containing all the arguments.

    The arguments should be specified the same way as for
    ``add_parser_arguments``.
    """
    if create:
        for key in required_args:
            required_args[key]['required'] = True
        add_parser_arguments(parser, required_args, group='required arguments')
    else:
        optional_args.update(required_args)
    add_parser_arguments(parser, optional_args)


def extract_arguments(args, prefix=DATA_PREFIX):
    """Return a dict of arguments created by `add_parser_arguments`.

    If the key in `args` contains two underscores, a nested dictionary will be
    created. Only keys starting with given prefix are examined. The prefix is
    stripped away and does not appear in the result.
    """
    data = {}
    for key, value in args.__dict__.iteritems():
        if key.startswith(prefix) and value is not None:
            parts = key[len(prefix):].split('__')
            # Think of `d` as a pointer into the resulting nested dictionary.
            # The `for` loop iterates over all parts of the key except the last
            # to find the proper dict into which the value should be inserted.
            # If the subdicts do not exist, they are created.
            d = data
            for p in parts[:-1]:
                assert p not in d or isinstance(d[p], dict)
                d = d.setdefault(p, {})
            # At this point `d` points to the correct dict and value can be
            # inserted.
            d[parts[-1]] = value if value != '' else None
    return data
