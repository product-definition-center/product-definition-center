#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

from . import BaseMessenger


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
