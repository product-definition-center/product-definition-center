#
# Copyright (c) 2017 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from datetime import date, datetime, timedelta
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from pdc.apps.release.models import Release
from pdc.apps.componentbranch.models import SLA
from pdc.apps.releaseschedule.models import ReleaseSchedule


def backend_url(viewname, *args):
    return 'http://testserver' + reverse(viewname, args=args)


class ReleaseScheduleAPITestCase(APITestCase):

    fixtures = [
        'pdc/apps/releaseschedule/fixtures/tests/release.json',
        'pdc/apps/releaseschedule/fixtures/tests/sla.json',
        'pdc/apps/releaseschedule/fixtures/tests/releaseschedule.json',
    ]

    def test_create(self):
        url = reverse('releaseschedule-list')
        data = {
            'release': 'test-release-0.1',
            'sla': 'bug_fixes',
            'date': '2017-01-01',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected = {
            'active': False,
            'date': '2017-01-01',
            'release': 'test-release-0.1',
            'sla': 'bug_fixes',
            'release_url': backend_url('release-detail', 'test-release-0.1'),
            'sla_url': backend_url('sla-detail', 2),
            'id': 2,
        }
        self.assertEqual(response.data, expected)

    def test_create_duplicate(self):
        # This release schedule already exists.
        url = reverse('releaseschedule-list')
        data = {
            'release': 'test-release-0.1',
            'sla': 'development',
            'date': '2017-01-01',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch(self):
        url = reverse('releaseschedule-detail', args=[1])
        changes = [
            ('date', '2018-01-01'),
            ('release', 'test-release-0.2'),
            ('sla', 'bug_fixes'),
        ]
        for change in changes:
            response = self.client.patch(url, dict([change]), format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['id'], 1)
            self.assertEqual(response.data[change[0]], change[1])

    def test_get(self):
        url = reverse('releaseschedule-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0], {
            'active': False,
            'date': '2017-01-01',
            'release': 'test-release-0.1',
            'sla': 'development',
            'release_url': backend_url('release-detail', 'test-release-0.1'),
            'sla_url': backend_url('sla-detail', 1),
            'id': 1,
        })

    def test_get_filter(self):
        url = reverse('releaseschedule-list')
        # Define some dates
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        day_after = today + timedelta(days=2)
        yesterday = today - timedelta(days=1)
        # Create test data
        release_1 = Release.objects.get(pk=1)
        release_2 = Release.objects.get(pk=2)
        sla_dev = SLA.objects.get(pk=1)
        sla_bug = SLA.objects.get(pk=2)
        sla_sec = SLA.objects.get(pk=3)
        expired_schedule_1 = ReleaseSchedule.objects.get(pk=1)
        active_schedule_1 = ReleaseSchedule.objects.create(
            release=release_1, sla=sla_bug, date=tomorrow)
        future_schedule_1 = ReleaseSchedule.objects.create(
            release=release_1, sla=sla_sec, date=day_after)
        expired_schedule_2 = ReleaseSchedule.objects.create(
            release=release_2, sla=sla_dev, date=yesterday)
        active_schedule_2 = ReleaseSchedule.objects.create(
            release=release_2, sla=sla_bug, date=tomorrow)
        future_schedule_2 = ReleaseSchedule.objects.create(
            release=release_2, sla=sla_sec, date=day_after)
        # Assert that we get all release schedules by default.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 6)
        # Filter on release
        response = self.client.get("{}?ordering=id&release=test-release-0.1".format(url))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(
            [result["id"] for result in response.data['results']],
            [expired_schedule_1.id, active_schedule_1.id, future_schedule_1.id]
        )
        # Filter on sla
        response = self.client.get("{}?ordering=id&sla=bug_fixes".format(url))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(
            [result["id"] for result in response.data['results']],
            [active_schedule_1.id, active_schedule_2.id])
        # Filter on active state
        response = self.client.get("{}?ordering=id&active=1".format(url))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(
            [result["id"] for result in response.data['results']],
            [
                active_schedule_1.id, future_schedule_1.id,
                active_schedule_2.id, future_schedule_2.id,
            ]
        )
        # Filter on date
        response = self.client.get(
            "{}?ordering=id&date_after={}".format(url, tomorrow.isoformat()))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(
            [result["id"] for result in response.data['results']],
            [active_schedule_1.id, future_schedule_1.id,
             active_schedule_2.id, future_schedule_2.id]
        )
        response = self.client.get(
            "{}?ordering=id&date_before={}".format(url, tomorrow.isoformat()))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(
            [
                result["id"] for result in response.data['results']
            ],
            [
                expired_schedule_1.id, active_schedule_1.id,
                expired_schedule_2.id, active_schedule_2.id,
            ]
        )

    def test_use_case_current_releases(self):
        # Get the current releases, defined by "releases that have an active
        # `bug_fixes` SLA".
        url = reverse('releaseschedule-list')
        # Define some dates
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)
        # Create test data
        release_1 = Release.objects.get(pk=1)
        release_2 = Release.objects.get(pk=2)
        release_3 = Release.objects.get(pk=3)
        sla_dev = SLA.objects.get(pk=1)
        sla_bug = SLA.objects.get(pk=2)
        # Release 1 is old
        ReleaseSchedule.objects.get(pk=1)
        ReleaseSchedule.objects.create(
            release=release_1, sla=sla_bug, date=yesterday)
        # Release 2 is current
        ReleaseSchedule.objects.create(
            release=release_2, sla=sla_dev, date=yesterday)
        ReleaseSchedule.objects.create(
            release=release_2, sla=sla_bug, date=tomorrow)
        # Release 3 is still in dev
        ReleaseSchedule.objects.create(
            release=release_3, sla=sla_dev, date=tomorrow)
        # Assert that we get all release schedules by default.
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        # Filter current releases
        response = self.client.get("{}?active=1&sla=bug_fixes".format(url))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(
            response.data['results'][0]["release"], "test-release-0.2")

    def test_use_case_default_slas(self):
        # Get the default SLAs for a release.
        url = reverse('releaseschedule-list')
        # Define some dates
        day1 = date(2018, 1, 1)
        day2 = date(2019, 1, 1)
        day3 = date(2020, 1, 1)
        # Create test data
        release = Release.objects.get(pk=1)
        sla_bug = SLA.objects.get(pk=2)
        sla_sec = SLA.objects.get(pk=3)
        sla_api = SLA.objects.create(name="stable_api")
        ReleaseSchedule.objects.create(
            release=release, sla=sla_bug, date=day1)
        ReleaseSchedule.objects.create(
            release=release, sla=sla_sec, date=day2)
        ReleaseSchedule.objects.create(
            release=release, sla=sla_api, date=day3)
        # Assert that we get all release schedules by default.
        response = self.client.get(
            "{}?ordering=date&release=test-release-0.1".format(url))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
        self.assertEqual(
            [
                (result["sla"], result["date"])
                for result in response.data['results']
            ], [
                ("development", "2017-01-01"),
                ("bug_fixes", "2018-01-01"),
                ("security_fixes", "2019-01-01"),
                ("stable_api", "2020-01-01")
            ])


class ReleaseScheduleModelTestCase(APITestCase):

    fixtures = [
        'pdc/apps/releaseschedule/fixtures/tests/release.json',
        'pdc/apps/releaseschedule/fixtures/tests/sla.json',
    ]

    def test_active(self):
        today = datetime.utcnow().date()
        release = Release.objects.get(pk=1)
        sla_dev = SLA.objects.get(pk=1)
        sla_bug = SLA.objects.get(pk=2)
        expired_schedule = ReleaseSchedule.objects.create(
            release=release, sla=sla_dev, date=(today - timedelta(days=1))
        )
        active_schedule = ReleaseSchedule.objects.create(
            release=release, sla=sla_bug, date=(today + timedelta(days=1))
        )
        self.assertFalse(expired_schedule.active)
        self.assertTrue(active_schedule.active)
