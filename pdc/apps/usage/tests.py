#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock

from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.authtoken.models import Token
from pdc.apps.common.test_utils import create_user
from . import models


class UsageTestCase(APITestCase):
    def setUp(self):
        admin = create_user('admin', is_super=True)
        admin_token, _ = Token.objects.get_or_create(user=admin)
        self.admin_token = 'Token %s' % admin_token

        user = create_user('user')
        user_token, _ = Token.objects.get_or_create(user=user)
        self.user_token = 'Token %s' % user_token

        self.now = timezone.now()

    @mock.patch('django.utils.timezone.now')
    def test_admin_is_not_logged(self, time_mock):
        time_mock.return_value = self.now
        self.client.get(reverse('api-root'), HTTP_AUTHORIZATION=self.admin_token)
        self.assertEqual(0, models.ResourceUsage.objects.count())
        admin = get_user_model().objects.get(username='admin')
        self.assertEqual(admin.last_connected, self.now)

    @mock.patch('django.utils.timezone.now')
    def test_user_access_time_is_updated(self, time_mock):
        time_mock.return_value = self.now
        self.client.get(reverse('api-root'), HTTP_AUTHORIZATION=self.user_token)
        user = get_user_model().objects.get(username='user')
        self.assertEqual(user.last_connected, self.now)

    @mock.patch('django.utils.timezone.now')
    def test_resource_usage_is_recorded(self, time_mock):
        time_mock.return_value = self.now
        self.client.get(reverse('api-root'), HTTP_AUTHORIZATION=self.user_token)
        user = get_user_model().objects.get(username='user')
        self.assertEqual(1, models.ResourceUsage.objects.count())
        record = models.ResourceUsage.objects.get(resource='APIRoot', method='GET')
        self.assertEqual(record.user, user)
        self.assertEqual(record.time, self.now)
