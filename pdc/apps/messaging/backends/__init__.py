#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#


class BaseMessenger(object):
    """
    Base class for messengers.

    Derived class should implement either `send_message` or `send_messages`.
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
