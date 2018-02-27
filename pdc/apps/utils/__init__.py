#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.conf import settings

import messaging


MESSENGERS = {
    'kombu': messaging.KombuMessenger,
    'fedmsg': messaging.FedmsgMessenger,
    'proton': messaging.ProtonMessenger,
    'stomp': messaging.StompMessenger,
    'test': messaging.TestMessenger,
}

# init messenger
messenger = MESSENGERS.get(settings.MESSAGE_BUS['MLP'], messaging.DummyMessenger)()
