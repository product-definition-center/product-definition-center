#
# Copyright (c) 2015,2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import absolute_import

import itertools
import json
import logging
import threading
import Queue

from django.conf import settings

from . import BaseMessenger

logger = logging.getLogger(__name__)


class RHMsgMessenger(BaseMessenger):
    def __init__(self):
        self.prefix = settings.MESSAGE_BUS['TOPIC_PREFIX']
        self.config = dict(
            certificate=settings.MESSAGE_BUS['CERTIFICATE'],
            private_key=settings.MESSAGE_BUS['CERTIFICATE'],
            trusted_certificates=settings.MESSAGE_BUS.get('CACERT'),
            urls=settings.MESSAGE_BUS['URLS'],
            timeout=settings.MESSAGE_BUS.get('CONNECTION_TIMEOUT'),
        )
        self.queue = Queue.Queue()
        self.worker = threading.Thread(target=self._worker)
        self.worker.daemon = True
        self.worker.start()

    def _make_headers(self, msg):
        """
        Extract all scalar values from the message root and new value and put
        them as headers.
        """
        headers = {}
        for prefix, obj in (('', msg), ('DATA:', msg.get('new_value', {}))):
            for key, value in obj.iteritems():
                if isinstance(value, (basestring, int, bool)) or value is None:
                    headers[prefix + key] = value

        return headers

    def send_messages(self, msgs):
        """
        Group messages by topic and send each group as one chunk.

        This can save a lot of time for bulk changes since there will be only
        one connection per group.
        """
        for topic, msgs in itertools.groupby(msgs, lambda x: x[0]):
            self.queue.put((topic, list(msgs)))

    def _worker(self):
        while True:
            topic, msgs = self.queue.get()
            self._send_message(topic, msgs)
            self.queue.task_done()

    def _send_message(self, topic, msgs):
        topic = '%s%s' % (self.prefix, topic)

        # Create a list of tuples (headers, JSON-encoded message body).
        to_send = [(self._make_headers(msg), json.dumps(msg)) for _, msg in msgs]
        logger.info('Sending %d messages to %s', len(to_send), topic)

        producer = _get_rhmsg_producer(**self.config)
        producer.through_topic(topic)
        try:
            producer.send_msgs(to_send)
        except Exception:
            logger.exception('Failed to send message to %s', topic)


def _get_rhmsg_producer(*args, **kwargs):
    """Helper function to simplify mocking the producer in tests."""
    import rhmsg.activemq.producer
    return rhmsg.activemq.producer.AMQProducer(*args, **kwargs)
