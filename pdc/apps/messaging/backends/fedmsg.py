#
# Copyright (c) 2015,2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import absolute_import

from . import BaseMessenger


class FedmsgMessenger(BaseMessenger):
    def __init__(self):
        import fedmsg
        self.messenger = fedmsg

    def send_message(self, topic, msg):
        topic = topic.strip('.')
        self.messenger.publish(topic=topic, msg=msg)
