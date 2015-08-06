#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from types import MethodType

import mock
from rest_framework.response import Response
from rest_framework import status
import unittest

from . import bulk_operations as bulk


class BulkOperationTestCase(unittest.TestCase):
    def setUp(self):
        self.request = mock.Mock()
        self.viewset = mock.Mock()
        self.viewset.create.__name__ = 'create'
        self.viewset.kwargs = {}
        self.viewset.lookup_field = 'key'

    def test_create_wrapper_with_single_object(self):
        wrapped = bulk.bulk_create_wrapper(self.viewset.create)
        self.viewset.create.return_value = 'Success'
        self.request.data = {'key': 'value'}
        result = wrapped(self.viewset, self.request)
        self.viewset.create.assert_called_with(self.viewset, self.request)
        self.assertEqual(result, 'Success')

    def test_create_wrapper_delegates_to_original(self):
        def view(_viewset, request, **kwargs):
            return Response(request._full_data.upper(), status=status.HTTP_201_CREATED)
        self.viewset.create = mock.Mock(side_effect=view)
        self.viewset.create.__name__ = 'create'
        wrapped = bulk.bulk_create_wrapper(self.viewset.create)
        self.request.data = ['foo', 'bar']
        result = wrapped(self.viewset, self.request)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.assertEqual(result.data, ['FOO', 'BAR'])
        self.viewset.create.assert_has_calls([mock.call(self.viewset, self.request),
                                              mock.call(self.viewset, self.request)])

    def test_create_wrapper_catches_exceptions(self):
        def view(viewset, _request, **kwargs):
            if viewset.counter == 2:
                raise Exception('BOOM')
            viewset.counter += 1
            return Response(status=status.HTTP_201_CREATED)

        self.viewset.counter = 0
        self.viewset.create = view
        wrapped = bulk.bulk_create_wrapper(self.viewset.create)
        self.request.data = ['foo', 'bar', 'baz', 'quux']
        with mock.patch('logging.getLogger') as getLogger:
            response = wrapped(self.viewset, self.request)
            getLogger.return_value.assert_called()
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_create_wrapper_aborts_on_bad_response(self):
        def view(viewset, _request, **kwargs):
            if viewset.counter == 2:
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'error'})
            viewset.counter += 1
            return Response(status=status.HTTP_201_CREATED)

        self.viewset.counter = 0
        self.viewset.create = view
        wrapped = bulk.bulk_create_wrapper(self.viewset.create)
        self.request.data = ['foo', 'bar', 'baz', 'quux']
        response = wrapped(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'invalid_data': 'baz', 'invalid_data_id': 2, 'detail': 'error'})

    def test_bulk_destroy(self):
        self.request.data = ['foo', 'bar', 'baz']
        self.viewset.destroy.return_value = Response(status=status.HTTP_204_NO_CONTENT)
        response = bulk.bulk_destroy_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.viewset.destroy.assert_has_calls([mock.call(self.request, key='foo'),
                                               mock.call(self.request, key='bar'),
                                               mock.call(self.request, key='baz')])

    def test_bulk_destroy_with_non_list_data(self):
        self.request.data = 'Ceci n\'est pas une list.'
        response = bulk.bulk_destroy_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_destroy_catches_exception(self):
        def view(viewset, _request, **kwargs):
            if viewset.counter == 2:
                raise Exception('BOOM')
            viewset.counter += 1
            return Response(status=status.HTTP_204_NO_CONTENT)

        self.viewset.counter = 0
        self.viewset.destroy = MethodType(view, self.viewset, mock.Mock)
        self.request.data = ['foo', 'bar', 'baz', 'quux']
        with mock.patch('logging.getLogger') as getLogger:
            response = bulk.bulk_destroy_impl(self.viewset, self.request)
            getLogger.return_value.assert_called()
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_bulk_destroy_aborts_on_bad_response(self):
        self.viewset.destroy.side_effect = [
            Response(status=status.HTTP_204_NO_CONTENT),
            Response(status=status.HTTP_204_NO_CONTENT),
            Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'error'}),
            Response(status=status.HTTP_204_NO_CONTENT),
        ]
        self.request.data = ['foo', 'bar', 'baz', 'quux']
        response = bulk.bulk_destroy_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_destroy_handles_duplicate_keys(self):
        self.viewset.destroy.side_effect = [
            Response(status=status.HTTP_204_NO_CONTENT),
            Response(status=status.HTTP_204_NO_CONTENT),
            Response(status=status.HTTP_204_NO_CONTENT),
            Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'Not found.'}),
        ]
        self.request.data = ['bar', 'foo', 'baz', 'foo']
        response = bulk.bulk_destroy_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.viewset.destroy.assert_has_calls([mock.call(self.request, key='bar'),
                                               mock.call(self.request, key='foo'),
                                               mock.call(self.request, key='baz')])

    def test_bulk_update(self):
        self.request.data = {'foo': {'key': 'val1'}, 'bar': {'key': 'val2'}, 'baz': {'key': 'val3'}}
        self.viewset.update.return_value = Response(status=status.HTTP_200_OK)
        response = bulk.bulk_update_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.viewset.update.assert_has_calls([mock.call(self.request, key='foo'),
                                              mock.call(self.request, key='bar'),
                                              mock.call(self.request, key='baz')],
                                             any_order=True)

    def test_bulk_update_on_non_dict(self):
        self.request.data = ['not', 'a', 'dict']
        response = bulk.bulk_update_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_update_catches_exception(self):
        def view(viewset, _request, **kwargs):
            if viewset.counter == 2:
                raise Exception('BOOM')
            viewset.counter += 1
            return Response(status=status.HTTP_200_OK)

        self.viewset.counter = 0
        self.viewset.update = MethodType(view, self.viewset, mock.Mock)
        self.request.data = {'foo': {'key': 'val1'}, 'bar': {'key': 'val2'}, 'baz': {'key': 'val3'}}
        with mock.patch('logging.getLogger') as getLogger:
            response = bulk.bulk_update_impl(self.viewset, self.request)
            getLogger.return_value.assert_called()
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_bulk_update_aborts_on_bad_response(self):
        self.viewset.update.side_effect = [
            Response(status=status.HTTP_200_OK),
            Response(status=status.HTTP_200_OK),
            Response(status=status.HTTP_400_BAD_REQUEST, data={'detail': 'error'}),
            Response(status=status.HTTP_200_OK),
        ]
        self.request.data = {'foo': {'key': 'val1'}, 'bar': {'key': 'val2'}, 'baz': {'key': 'val3'}}
        response = bulk.bulk_update_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.viewset.update.assert_has_calls([mock.call(self.request, key='foo'),
                                              mock.call(self.request, key='bar'),
                                              mock.call(self.request, key='baz')],
                                             any_order=True)

    def test_bulk_partial_update_on_non_dict(self):
        self.request.data = ['not', 'a', 'dict']
        response = bulk.bulk_update_impl(self.viewset, self.request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


if __name__ == '__main__':
    unittest.main()
