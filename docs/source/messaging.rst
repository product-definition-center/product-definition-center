.. _messaging:

Messaging
=========

Overview
--------

Messaging enables PDC to send out useful informations to message bus so that other
systems can subscribe and deal with them.

Current design is based on Django Middleware system, by implementing our MsgMiddleware,
we could initialize a message queue for every incoming request during the ``process_request``,
and push generated messages into it while processing the request in the view,
if no error occurs, before response get returned to user, we pop out all the messages
and invoke the configured backend to send them to the Message Bus.

PDC Messaging Overview and Dataflow::

                     User Request           User Response
                          +                      ^
    +-----+               |                      |
    | PDC |               |                      |
    +-----+------------------------------------------------------------------+
    |                     v                      |                           |
    |   +---------------+ |                      |                           |
    |   | MsgMiddleware | |                      ^                           |
    |   +---------------+-------------------------------+   +------------+   |
    |   |                 |                      |      |   | Messenger  |   |
    |   |     +-----------v-+ Init       +-------+----+ |   +------------+   |      Message
    |   |     | Process Req +->+      +-->Process Rsp +----->            +--------> Bus
    |   |     +-----------+-+  |      |  +------------+ |   | +send_msgs |   |      Server
    |   |                 |    |      ^ Dequeue  |      |   |            |   |
    |   +----------------------------------------^------+   +------------+   |
    |                     |    |      |          |                           |
    |                     | +--v------+---+      |                           |
    |                     | |  Msg Queue  |      |                           |
    |   +--------+        | +----+--------+      ^                           |
    |   |  View  |        |      ^ Enqueue       |                           |
    |   +--------+--------------------------------------+                    |
    |   |                 |      |               |      |                    |
    |   |                 v -----+-------------->+      |                    |
    |   |                                               |                    |
    |   +-----------------------------------------------+                    |
    +------------------------------------------------------------------------+


Supported Messengers
--------------------


There are two messengers that PDC provides, you should choose which one to use
according to your messaging infrastructure. Also you could write your own
messenger based on your own requirements.

Once you got the answer what left is to configure ``MESSAGE_BUS`` item in the
settings file accordingly. The key determining which backend to use is
``BACKEND``, whose value should be a dotted module path pointing to the
messenger implementation.

Following is the brief introduction of each messenger along with their settings
examples, it will help you to know which one to use and how to configure it as
well.

#. ``DummyMessenger`` (Default)

   If you do not need to send messages out, you could just omit the
   configuration out entirely. The messages will be logged, but not sent
   anyhere.


#. ``FedmsgMessenger``

   If you want to send PDC messages to Fedora Infrastructure Message Bus, you
   should choose ``FedmsgMessenger``.

   ``fedmsg`` needs to be installed.

   ::

        MESSAGE_BUS = {
            'BACKEND': 'pdc.apps.messaging.backends.fedmsg.FedmsgMessenger',
        }


#. ``RHMsgMessenger``

   This messenger is built on top of ``python-rhmsg`` library and is used to
   send notification to Red Hat's internal message bus.

   To use it, the configuration should specify a list of message brokers, a
   path to a certificate used for authentication and a topic prefix to use for
   all messages. See the example below for details.

   The file pointed to by ``CERTIFICATE`` should contain both the public
   certificate and the private key in PEM format.

   ::

        MESSAGE_BUS = {
            'BACKEND': 'pdc.apps.messaging.backends.rhmsg.RHMsgMessenger',
            # The brokers will be tried in random order. If connection can not
            # be made in a given timeout, another URL is tried.
            'URLS': [
                'amqps://broker01.example.com:5671',
                'amqps://broker02.example.com:5671',
            ],
            # How long to wait for each broker. The default is 60 seconds.
            'CONNECTION_TIMEOUT': 5,

            'CERTIFICATE': '/etc/pdc/certificate.pem',
            'CACERT': '/etc/pdc/authoritycert.crt',

            # This value is prepended to topic of all messages.
            'TOPIC_PREFIX': 'VirtualTopic.eng.pdc',
        }


To Be Improved
--------------

* Better Error handling
* Message structure refine
* Transaction based Messaging
* Persistent messages that failed to send out
* Non-blocking
