#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings


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
