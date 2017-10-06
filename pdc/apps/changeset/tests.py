#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from mock import Mock, call, patch

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from .middleware import ChangesetMiddleware
from .middleware import logger as changeset_logger


class ChangesetMiddlewareTestCase(TestCase):
    def setUp(self):
        self.cm = ChangesetMiddleware()
        self.request = Mock()
        setattr(self.request, "method", "POST")

    def test_passing_arguments(self):
        self.request.user.is_authenticated = lambda: False
        self.request.META.get = lambda x, y: y
        func = Mock()
        func.__name__ = "Mock"
        func.return_value = 123
        with patch("pdc.apps.changeset.models.Changeset") as changeset:
            ret = self.cm.process_view(self.request, func, [1, 2, 3], {'arg': 'val'})
            self.assertTrue(func.called)
            self.assertEqual(ret, 123)
            self.assertEqual(func.call_args, call(self.request, 1, 2, 3, arg='val'))
            self.assertEqual(changeset.mock_calls[0], call(author=self.request.user, comment=None))
            self.assertEqual(changeset.mock_calls[1], call().commit())

    def test_no_commit_with_exception(self):
        self.request.user.is_authenticated = lambda: False
        self.request.META.get = lambda x, y: y
        func = Mock()
        func.__name__ = "Mock"
        func.side_effect = Exception("Boom!")
        changeset_logger.error = Mock()
        with patch("pdc.apps.changeset.models.Changeset") as changeset:
            self.assertRaises(Exception, self.cm.process_view, self.request, func, [], {})
            self.assertTrue(func.called)
            self.assertEqual(changeset.mock_calls, [call(author=self.request.user, comment=None)])
            self.assertTrue(changeset_logger.error.called)


class ChangesetRESTTestCase(APITestCase):
    fixtures = ['pdc/apps/changeset/fixtures/tests/changeset.json',
                "pdc/apps/component/fixtures/tests/bugzilla_component.json"]

    def test_get(self):
        url = reverse('changeset-detail', args=[1])
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('changes')), 2)
        self.assertEqual(response.data.get("id"), 1)

    def test_list_order(self):
        url = reverse('changeset-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results')
        self.assertTrue(results[0].get('committed_on') > results[1].get('committed_on'))

    def test_query(self):
        url = reverse('changeset-list')
        response = self.client.get(url + '?resource=contact', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_with_multiple_values(self):
        url = reverse('changeset-list')
        response = self.client.get(url + '?resource=contact&resource=person', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_query_with_wrong_resource(self):
        url = reverse('changeset-list')
        response = self.client.get(url + '?resource=nonexists', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_with_correct_datetimeformat(self):
        url = reverse('changeset-list')
        response = self.client.get(url + '?changed_since=2015-02-03T02:55:18', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_with_incorrect_datetimeformat(self):
        url = reverse('changeset-list')
        response = self.client.get(url + '?changed_since=20150203T02:55:18', format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_with_pdc_change_comment(self):
        url = reverse('changeset-list')
        response = self.client.get(url + '?comment=change', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_create_with_pdc_change_comment(self):
        url = reverse('bugzillacomponent-list')
        data = {'name': 'bin', 'parent_pk': 1}
        extra = {'HTTP_PDC_CHANGE_COMMENT': 'New bugzilla component'}
        response = self.client.post(url, data, format='json', **extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url1 = reverse('changeset-list')
        response1 = self.client.get(url1 + '?comment=new', format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['count'], 1)

    def test_bulk_create_with_pdc_change_comment(self):
        url = reverse('bugzillacomponent-list')
        data = [{'name': 'bin', 'parent_pk': 1}, {'name': 'bin1', 'parent_pk': 2}]
        extra = {'HTTP_PDC_CHANGE_COMMENT': 'New bugzilla components'}
        response = self.client.post(url, data, format='json', **extra)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        url1 = reverse('changeset-list')
        response1 = self.client.get(url1 + '?comment=components', format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['count'], 1)
        self.assertEqual(len(response1.data.get('results')[0].get('changes')), 2)
