#
# Copyright (c) 2015,2018 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#

import json
import logging

from . import BaseMessenger

logger = logging.getLogger(__name__)


class DummyMessenger(BaseMessenger):

    def send_message(self, topic, msg):
        logger.info('Sending to %s:\n%s' % (topic, json.dumps(msg, sort_keys=True, indent=2)))
