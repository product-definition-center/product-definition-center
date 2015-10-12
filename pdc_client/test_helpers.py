# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock
import math
import functools
from StringIO import StringIO
import contextlib
import unittest
import os
import json
import types


class PathAccumulator(object):
    def __init__(self, path, api):
        self.api = api
        self.path = path

    def _getattr(self, key):
        if key == '_':
            self.api.validate_path(self.path)
            return self.api
        self.path += '/' + str(key)
        return self

    def __getattr__(self, key):
        return self._getattr(key)

    def __getitem__(self, key):
        return self._getattr(key)


class MockAPI(object):
    """Representation of mocked API.

    This class replaces the PDCClient in code. Without any additional
    specification, all calls to the API will fail. You can use the
    `add_endpoint` method to add valid points where the client can connect and
    the data it should receive from there.

    Validation of the requests should use the `calls` attribute, which contains
    a dictionary mapping resource URLs to lists of request details. Each
    request details is a tuple depending on actual method.

        (GET,   {filters})
        (POST,  {request data})
        (PATCH, {request data})
    """
    def __init__(self):
        self.endpoints = {}
        self.calls = {}

    def add_endpoint(self, resource, method, data):
        """Add allowed point of connection.

        Keyword arguments:
        :param resource:    resource url without initial and trailing slash
        :param method:      expected HTTP method
        :paramtype method:  string
        :param data:        response to client

        If the data is a list, it will be returned paginated and the mocked
        end-point will handle `page` query filter.
        """
        self.endpoints.setdefault(resource, {})[method] = data

    def validate_path(self, path):
        assert path in self.endpoints, 'client requested unknown resource /%s/' % path
        self.will_call = path

    def __getattr__(self, key):
        return PathAccumulator(key, self)

    def __getitem__(self, key):
        return PathAccumulator(key, self)

    def __call__(self, *args, **kwargs):
        if len(args) == 2 and args[0] == 'PATCH':
            return self._handle_patch(args[1])
        if len(args) == 1:
            return self._handle_post(args[0])
        elif len(args) == 0:
            return self._handle_get(kwargs)

    def _handle_post(self, data):
        self.calls.setdefault(self.will_call, []).append(('POST', data))
        return self.endpoints[self.will_call]['POST']

    def _handle_get(self, filters):
        data = self.endpoints[self.will_call]['GET']
        self.calls.setdefault(self.will_call, []).append(('GET', filters))
        if isinstance(data, list):
            page = filters.get('page', 1)
            page_size = 20
            pages = int(math.ceil(float(len(data)) / page_size))
            data = data[(page - 1) * page_size:(page - 1) * page_size + page_size]
            return {
                'count': len(data),
                'next': None if (page == pages or not pages) else self._fmt_url(page + 1),
                'previous': None if (page == 1 or not pages) else self._fmt_url(page - 1),
                'results': data
            }
        return data

    def _handle_patch(self, data):
        self.calls.setdefault(self.will_call, []).append(('PATCH', data))
        return self.endpoints[self.will_call]['PATCH']

    def _fmt_url(self, page):
        return 'http://testserver/?page={}'.format(page)

    def __iadd__(self, data):
        self._handle_patch(data)


def mock_api(func):
    @functools.wraps(func)
    def wrapper(self):
        with mock.patch('pdc_client.PDCClient') as cls:
            api = MockAPI()
            cls.return_value = api
            return func(self, api)
    return wrapper


class CLIMetaClass(type):
    """Automatically wrap all test methods in `mock_api` decorator.
    """
    def __new__(cls, name, bases, attrs):
        for attr_name, attr_value in attrs.iteritems():
            if isinstance(attr_value, types.FunctionType) and attr_name.startswith('test_'):
                attrs[attr_name] = mock_api(attr_value)

        return super(CLIMetaClass, cls).__new__(cls, name, bases, attrs)


class CLITestCase(unittest.TestCase):
    """Base class for test cases of client UI.

    All test methods should accept one additional argument, which represents
    the mocked API and is an instance of MockAPI class. The test will not have
    any access to real server.
    """
    __metaclass__ = CLIMetaClass

    @property
    def _data_dir(self):
        return os.path.join(*self.__class__.__module__.split('.')[:-1] + ['data'])

    def _data_file(self, file):
        with open(os.path.join(self._data_dir, file), 'r') as f:
            return f.read()

    @contextlib.contextmanager
    def expect_output(self, file, parse_json=False):
        """Expect contents of the with statement to print contents of file.

        The file is looked up relatively in data subdir of the directory where
        the test is located. When the code finishes, the printed output and
        contents of the file are compared line by line.

        By using the `parse_json` argument, it is possible to instead parse the
        output and file as JSON and compare the resulting datastructure.
        """
        contents = self._data_file(file)
        patcher = mock.patch('sys.stdout', new_callable=StringIO)
        output = patcher.start()
        yield
        patcher.stop()
        if parse_json:
            self.assertEqual(json.loads(output.getvalue()),
                             json.loads(contents))
        else:
            self.assertEqual(output.getvalue().split('\n'), contents.split('\n'))

    @contextlib.contextmanager
    def expect_failure(self):
        """Assert that the code in with block calls `sys.exit()` with value >0.

        This also silences any output to stderr.
        """
        class StopCode(Exception):
            """This exception will be raised instead of exiting the program."""
            def __init__(self, exit_code):
                self.exit_code = exit_code

        def stop_code(arg):
            raise StopCode(arg)

        with mock.patch('sys.exit') as exit:
            exit.side_effect = stop_code
            try:
                with mock.patch('sys.stderr'):
                    yield
            except StopCode as exc:
                self.assertGreater(exc.exit_code, 0)
            exit.assert_called()
