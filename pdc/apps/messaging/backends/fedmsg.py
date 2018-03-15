#
# Copyright (c) 2015,2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from __future__ import absolute_import

import fedmsg

from . import BaseMessenger


class FedmsgMessenger(BaseMessenger):
    def send_message(self, topic, msg):
        topic = topic.strip('.')
        fedmsg.publish(topic=topic, msg=msg)
