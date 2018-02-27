#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import json

from django.conf import settings
from django.utils import six

import logging

logger = logging.getLogger(__name__)


class DummyMessenger(object):
    def __init__(self):
        pass

    def send_message(self, topic, msg):
        pass


class KombuMessenger(object):
    def __init__(self):
        from kombu import Connection, Exchange
        self.conn = Connection(settings.MESSAGE_BUS['URL'],
                               **settings.MESSAGE_BUS.get('OPTIONS', {}))
        self.exchange = Exchange(**settings.MESSAGE_BUS['EXCHANGE'])
        self.messenger = self.conn.Producer()

    def send_message(self, topic, msg):
        self.messenger.publish(msg, exchange=self.exchange, routing_key=topic)


class FedmsgMessenger(object):
    def __init__(self):
        import fedmsg
        self.messenger = fedmsg

    def send_message(self, topic, msg):
        topic = topic.strip('.')
        if isinstance(msg, six.string_types):
            msg = json.loads(msg)
        self.messenger.publish(topic=topic, msg=msg)


class ProtonMessenger(object):
    def __init__(self):
        import proton
        self.messenger = proton.Messenger()
        self.messenger.certificate = settings.MESSAGE_BUS['CERT_FILE']
        self.messenger.private_key = settings.MESSAGE_BUS['KEY_FILE']
        self.messenger.start()
        self.message = proton.Message()

    def send_message(self, topic, msg):
        self.message.address = settings.MESSAGE_BUS['URL'] + topic
        self.message.body = msg
        self.messenger.put(self.message)
        self.messenger.send()


class StompMessenger(object):
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
                self.connection.send(body=msg, destination=address,
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


class TestMessenger(object):
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
