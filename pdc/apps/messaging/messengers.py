#
# Copyright (c) 2015,2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import itertools
import json
import threading
import Queue

from django.conf import settings

import logging

logger = logging.getLogger(__name__)


class BaseMessenger(object):
    """
    Base class for messengers.

    Children class should implement either `send_message` or `send_messages`.
    """

    def send_message(self, topic, msg):
        raise NotImplementedError(
            'Child class must implement send_message or send_messages method.')

    def send_messages(self, msgs):
        """
        Send multiple messages via `send_messages` method.

        Override this method if your messenger can do this more efficiently.
        """
        for (topic, msg) in msgs:
            self.send_message(topic, msg)


class DummyMessenger(BaseMessenger):

    def send_message(self, topic, msg):
        logger.info('Sending to %s:\n%s' % (topic, json.dumps(msg, sort_keys=True, indent=2)))


class KombuMessenger(BaseMessenger):
    def __init__(self):
        from kombu import Connection, Exchange
        self.conn = Connection(settings.MESSAGE_BUS['URL'],
                               **settings.MESSAGE_BUS.get('OPTIONS', {}))
        self.exchange = Exchange(**settings.MESSAGE_BUS['EXCHANGE'])
        self.messenger = self.conn.Producer()

    def send_message(self, topic, msg):
        self.messenger.publish(json.dumps(msg), exchange=self.exchange, routing_key=topic)


class FedmsgMessenger(BaseMessenger):
    def __init__(self):
        import fedmsg
        self.messenger = fedmsg

    def send_message(self, topic, msg):
        topic = topic.strip('.')
        self.messenger.publish(topic=topic, msg=msg)


class ProtonMessenger(BaseMessenger):
    def __init__(self):
        import proton
        self.messenger = proton.Messenger()
        self.messenger.certificate = settings.MESSAGE_BUS['CERT_FILE']
        self.messenger.private_key = settings.MESSAGE_BUS['KEY_FILE']
        self.messenger.start()
        self.message = proton.Message()

    def send_message(self, topic, msg):
        self.message.address = settings.MESSAGE_BUS['URL'] + topic
        self.message.body = json.dumps(msg)
        self.messenger.put(self.message)
        self.messenger.send()


class StompMessenger(BaseMessenger):
    def __init__(self):
        import stomp
        self.connection = stomp.Connection(
            host_and_ports=settings.MESSAGE_BUS['HOST_AND_PORTS'],
            use_ssl=True,
            ssl_key_file=settings.MESSAGE_BUS['KEY_FILE'],
            ssl_cert_file=settings.MESSAGE_BUS['CERT_FILE'],
        )
        self.connected = self.do_connect()

    def do_connect(self):
        try:
            self.connection.start()
            self.connection.connect()
        except Exception, e:
            logger.warn("StompMessenger connection exception(%s): %s." % (type(e), e))
            return False
        return True

    def send_message(self, topic, msg):
        address = '/topic/' + settings.MESSAGE_BUS['TOPIC'] + str(topic)
        if self.connected or self.do_connect():
            try:
                self.connection.send(body=json.dumps(msg), destination=address,
                                     headers={'persistent': 'true'},
                                     auto='true')
            except Exception, e:
                logger.warn("Send Message exception(%s): %s." % (type(e), e))
        else:
            logger.warn("Send Message exception: Failed to Connect to Messaging Server.")


class TestListener(object):
    """
    Context manager for messages from TestMessenger.
    """
    def __init__(self, messenger):
        self.messenger = messenger
        self.messages = []

    def __enter__(self):
        self.messenger.listeners.append(self)
        return self.messages

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.messenger.listeners.remove(self)


class TestMessenger(BaseMessenger):
    """
    Processes messages from message bus for tests.

    ::

        with messenger.listen() as messages:
            # Make requests ...
            topic, msg = messages[0]
    """
    def __init__(self):
        self.listeners = []

    def send_message(self, topic, msg):
        for listener in self.listeners:
            listener.messages.append((topic, msg))

    def listen(self):
        return TestListener(self)


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
