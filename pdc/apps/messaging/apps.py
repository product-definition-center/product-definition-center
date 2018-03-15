#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string


class MessagingConfig(AppConfig):
    name = 'pdc.apps.messaging'

    def ready(self):
        backend = settings.MESSAGE_BUS.get('BACKEND')
        if not backend:
            # Drop this block in next version and instead directly fall on
            # DummyMessenger.
            MESSENGERS = {
                'fedmsg': 'pdc.apps.messaging.backends.fedmsg.FedmsgMessenger',
                'test': 'pdc.apps.messaging.backends.capture.TestMessenger',
                'rhmsg': 'pdc.apps.messaging.backends.rhmsg.RHMsgMessenger',
            }
            backend = MESSENGERS.get(settings.MESSAGE_BUS['MLP'],
                                     'pdc.apps.messaging.backends.dummy.DummyMessenger')

        cls = import_string(backend)
        self.messenger = cls()
