# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import mock
from django.test import TestCase, override_settings


@override_settings(MESSAGE_BUS={
    'MLP': 'rhmsg',
    'TOPIC_PREFIX': 'eng.pdc',
    'CERTIFICATE': 'foo.pem',
    'CACERT': 'cacert.crt',
    'URLS': ['amqps://broker.example.com'],
    'CONNECTION_TIMEOUT': 30,
})
class ComposeModelTestCase(TestCase):

    def setUp(self):
        from . import messengers
        with mock.patch('threading.Thread') as t:
            self.t = t
            self.m = messengers.RHMsgMessenger()

    def test_put_to_queue(self):
        self.m.send_messages([('.t1', {'a': 'b'})])

        self.assertEqual(self.m.queue.get(),
                         ('.t1', [('.t1', {'a': 'b'})]))
        self.assertTrue(self.m.queue.empty())
        self.t.assert_called_once_with(target=self.m._worker)
        self.t.return_value.start.assert_called_once()
        self.assertTrue(self.t.return_value.daemon)

    def test_group_same_topic(self):
        self.m.send_messages([('.t1', {'a': 'b'}), ('.t1', {'c': 'd'})])

        self.assertEqual(self.m.queue.get(),
                         ('.t1', [('.t1', {'a': 'b'}), ('.t1', {'c': 'd'})]))
        self.assertTrue(self.m.queue.empty())

    def test_no_group_same_topic(self):
        self.m.send_messages([('.t1', {'a': 'b'}), ('t2', {'c': 'd'})])

        self.assertEqual(self.m.queue.get(),
                         ('.t1', [('.t1', {'a': 'b'})]))
        self.assertEqual(self.m.queue.get(),
                         ('t2', [('t2', {'c': 'd'})]))
        self.assertTrue(self.m.queue.empty())

    @mock.patch('pdc.apps.messaging.messengers._get_rhmsg_producer')
    @mock.patch('pdc.apps.messaging.messengers.logger')
    def test_send(self, mock_logger, mock_get_producer):
        self.m._send_message('.t1', [('.t1', {'a': 'b'})])

        self.assertEqual(
            mock_get_producer.call_args_list,
            [mock.call(urls=['amqps://broker.example.com'],
                       private_key='foo.pem',
                       certificate='foo.pem',
                       trusted_certificates='cacert.crt',
                       timeout=30)]
        )

        self.assertEqual(
            mock_get_producer.return_value.mock_calls,
            [mock.call.through_topic('eng.pdc.t1'),
             mock.call.send_msgs([({'a': 'b'}, '{"a": "b"}')])
             ]
        )

    @mock.patch('pdc.apps.messaging.messengers._get_rhmsg_producer')
    @mock.patch('pdc.apps.messaging.messengers.logger')
    def test_send_fail(self, mock_logger, mock_get_producer):
        def boom(*args, **kwargs):
            raise Exception('Boom')

        mock_get_producer.return_value.send_msgs.side_effect = boom

        try:
            self.m._send_message('.t1', [('.t1', {'a': 'b'})])
        except Exception:
            self.fail('Unexpected exception was raised')

    @mock.patch('pdc.apps.messaging.messengers._get_rhmsg_producer')
    @mock.patch('pdc.apps.messaging.messengers.logger')
    def test_send_with_headers(self, mock_logger, mock_get_producer):
        self.m._send_message('.t1', [('.t1', {'a': 'b', 'new_value': {'c': 'd'}})])

        self.assertEqual(
            mock_get_producer.return_value.mock_calls,
            [mock.call.through_topic('eng.pdc.t1'),
             mock.call.send_msgs([({'a': 'b', 'DATA:c': 'd'},
                                   '{"a": "b", "new_value": {"c": "d"}}')])
             ]
        )
