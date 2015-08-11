#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings

from .messaging import (DummyMessenger, KombuMessenger, FedmsgMessenger,
                        ProtonMessenger, StompMessenger)


MESSENGERS = {
    'kombu': KombuMessenger,
    'fedmsg': FedmsgMessenger,
    'proton': ProtonMessenger,
    'stomp': StompMessenger,
}

# init messenger
messenger = MESSENGERS.get(settings.MESSAGE_BUS['MLP'], DummyMessenger)()
