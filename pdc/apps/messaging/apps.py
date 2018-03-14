#
# Copyright (c) 2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from django.apps import AppConfig
from django.conf import settings


class MessagingConfig(AppConfig):
    name = 'pdc.apps.messaging'

    def ready(self):
        from . import messengers

        MESSENGERS = {
            'kombu': messengers.KombuMessenger,
            'fedmsg': messengers.FedmsgMessenger,
            'proton': messengers.ProtonMessenger,
            'stomp': messengers.StompMessenger,
            'test': messengers.TestMessenger,
        }

        # init messenger
        self.messenger = MESSENGERS.get(settings.MESSAGE_BUS['MLP'],
                                        messengers.DummyMessenger)()
