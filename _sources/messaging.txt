.. _messaging:

Messaging
=========

Overview
--------

Messaging enables PDC to send out useful informations to message bus so that other
systems can subscribe and deal with them.

Current design is based on Django Middleware system, by implementing our MsgMiddleware,
we could initialize a message queue for every incoming request during the `process_request`,
and push generated messages into it while processing the request in the view,
if no error occurs, before response get returned to user, we pop out all the messages
and invoke `Messenger` to send them to the Message Bus.

PDC Messaging Overview and Dataflow::

                     User Request           User Response
                          +                      ^
    +-----+               |                      |
    | PDC |               |                      |
    +-----+-----------------------------------------------------------------+
    |                     v                      |                          |
    |   +---------------+ |                      |                          |
    |   | MsgMiddleware | |                      ^                          |
    |   +---------------+-------------------------------+   +-----------+   |
    |   |                 |                      |      |   | Messenger |   |
    |   |     +-----------v-+ Init       +-------+----+ |   +-----------+   |      Message
    |   |     | Process Req +->+      +-->Process Rsp +----->           +--------> Bus
    |   |     +-----------+-+  |      |  +------------+ |   | +send_msg |   |      Server
    |   |                 |    |      ^ Dequeue  |      |   |           |   |
    |   +----------------------------------------^------+   +-----------+   |
    |                     |    |      |          |                          |
    |                     | +--v------+---+      |                          |
    |                     | |  Msg Queue  |      |                          |
    |   +--------+        | +----+--------+      ^                          |
    |   |  View  |        |      ^ Enqueue       |                          |
    |   +--------+--------------------------------------+                   |
    |   |                 |      |               |      |                   |
    |   |                 v -----+-------------->+      |                   |
    |   |                                               |                   |
    |   +-----------------------------------------------+                   |
    +-----------------------------------------------------------------------+


Supported Messengers
--------------------

::

                                         +----------------------------------+
                                         |           PDC Messenger          |
                                         +----------------------------------+
                                         |  + __init__()                    |
                                         |  + send_message(topic, msg)      |
                                         +----------------------------------+
                                             ^    ^       ^        ^    ^
                                             |    |       |        |    |
                   +-------------------------+    |       |        |    +-------------------------+
                   |                   +--------->+       |        +<---------+                   |
                   |                   |                  |                   |                   |
    +--------------+-+ +---------------+----+ +-----------+--------+ +--------+--------------+ +--+--------------------+
    | DummyMessenger | |  FedmsgMessenger   | |  KombuMessenger    | |    ProtonMessenger    | |     StompMessenger    |
    +----------------+ +--------------------+ +--------------------+ +-----------------------+ +-----------------------+

There are five messengers that PDC provided, you should choose which one to use according to your messaging
infrastructure. Also you could write your own messenger based on your own requirements.

Once you got the answer what left is to configure `MESSAGE_BUS` item in the `settings` file accordingly.

Following is the brief introduction of each messenger along with their settings examples, it will help you
to know which one to use and how to configure it as well.

#. `DummyMessenger` (Default)

   If you do not need to send messages out, you could just leave the `MLP` (Messaging Library Package) to empty string
   to use the `DummyMessenger`.

   e.g.

   ::

        # Messaging Bus Config
        MESSAGE_BUS = {
            # MLP: Messaging Library Package
            'MLP': '',
        }

#. `FedmsgMessenger`

   If you want to send PDC messages to Fedora Infrastructure Message Bus, you should choose `FedmsgMessenger` by setting
   the `MLP` to 'fedmsg'.

   `fedmsg` needs to be installed.

   `FedmsgMessenger` config example::

        # Messaging Bus Config
        MESSAGE_BUS = {
            # MLP: Messaging Library Package
            'MLP': 'fedmsg',
        }

#. `KombuMessenger`

   `Kombu` is a messaging library for Python. It supports AMQP(v0.9) and several message server solutions by using
   pluggable transports.

   NOTE: Not support AMQP(v1.0), so if you're using some messaging server implements AMQP(v1.0), like ActiveMQ, then
         you should use `ProtonMessenger` instead.

   `kombu` and related transport client library(like `py-amqp`, `librabbitmq`, or `qpid-python`) need to be installed.

   To use `KombuMessenger`, you need to add some more items in the settings, including `URL` of
   the broker, `EXCHANGE` and `OPTIONS`.

   e.g.

   ::

        # Messaging Bus Config
        MESSAGE_BUS = {
            # `kombu` config example:
            'MLP': 'kombu',
            'URL': 'amqp://guest:guest@example.com:5672//',
            'EXCHANGE': {
                'name': 'pdc',
                'type': 'topic',
                'durable': False
            },
            'OPTIONS': {
                # Set these two items to config `kombu` to use ssl.
                'login_method': 'EXTERNAL',
                'ssl': {
                    'ca_certs': '',
                    'keyfile': '',
                    'certfile': '',
                    'cert_reqs': 2,  # ssl.CERT_REQUIRED,
                }
            }
        }

#. `ProtonMessenger`

   Qpid-Proton supports AMQP(v1.0), and as if you're connecting to message server, like ActiveMQ, that supports
   AMQP(v1.0), `ProtonMessenger` should be your choice.

   NOTE: current implementation does not support multi endpoints failover.

   `qpid-proton` needs to be installed.

   `ProtonMessenger` config example::

       # Messaging Bus Config
       MESSAGE_BUS = {
           'MLP': 'proton',
           'URL': 'amqps://example.com:5671/com.redhat.pdc',
           'CERT_FILE': '',
           'KEY_FILE': '',
       }

#. `StompMessenger` (Recommended)

   `STOMP` is another message protocol that very simple and easy to implement as a client. So if `STOMP` over `AMQP` is
   acceptable for your application, we recommend you to use `StompMessenger` as it supports multi-endpoints failover.

   `stomp.py` needs to be installed.

   `StompMessenger` config example::

        # Messaging Bus Config
        MESSAGE_BUS = {
            # `stomp` config items:
            'MLP': 'stomp',
            'HOST_AND_PORTS': [
                ('stomp.example1.com', 61613),
                ('stomp.example2.com', 61613),
                ('stomp.example3.com', 61613),
            ],
            'TOPIC': 'pdc',
            'CERT_FILE': '',
            'KEY_FILE': '',
        }


To Be Improved
--------------

* Better Error handling
* Message structure refine
* Transaction based Messaging
* Persistent messages that failed to send out
* Non-blocking
