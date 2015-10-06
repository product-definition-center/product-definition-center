.. _pdc_client:

PDC Client
==========

PDC Client is a shell CLI that make it easier to access data from PDC servers.


Installation
------------

You can obtain the client from the same repository where PDC server is.


Configuration
-------------

The client can read server connection details from a configuration file. The
configuration file should be located in ``/etc/pdc/client_config.json`` or in
``~/.config/pdc/client_config.json``. If both files are present, the system one
is loaded first and the user configuration is applied on top of it (to add
other options or overwrite existing ones).

The configuration file should contain a JSON object, which maps server name to
JSON object with details. The name is an arbitrary string used at client run
time to identify which server you want to connect to.

The details of a single server must contain at least one key: ``host`` which
specifies the URL to the API root (e.g. ``http:://localhost:8000/rest_api/v1/``
for local instance).

Other possible keys are:

``token``
    If specified, this token will be used for authentication. The client will
    not try to obtain any token from the server.

``insecure``
    If set to ``true``, server certificate will not be validated.

``develop``
    When set to ``true``, the client will not use any authentication at all,
    not requesting a token nor sending any token with the requests. This is
    only useful for working with servers which don't require authentication.


Example system configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This config defines connection to development server running on localhost and a
production server. ::

    {
        "local": {
            "host": "http://localhost:8000/rest_api/v1/",
            "develop": true,
            "insecure": false
        },
        "prod": {
            "host": "https://pdc.example.com/rest_api/v1/",
        }
    }


Usage
-----

The client package contains two separate clients. Both contain extensive
built-in help. Just run the executable with ``-h`` or ``--help`` argument.

``pdc_client``
~~~~~~~~~~~~~~

This is a very simple client. Essentially this is just a little more convenient
than using ``curl`` manually. Each invocation of this client obtains a token
and then performs a single request.

This client is not meant for direct usage, but just as a helper for integrating
with PDC from languages where it might be easier than performing the network
requests manually.

``pdc``
~~~~~~~

This is much more user friendly user interface. A single invocation can perform
multiple requests depending on what subcommand you used.


Known Issues
------------

Kerberos
~~~~~~~~

Under enterprise network, `Reverse DNS mismatches
<http://web.mit.edu/Kerberos/www/krb5-latest/doc/admin/princ_dns.html#reverse-dns-mismatches>`_
may cause problems authenticating with Kerberos.

If you can successfully run ``kinit`` but not authenticate yourself to PDC
servers, check ``/etc/krb5.conf`` and make sure that ``rdns`` is set to false
in ``libdefaults`` section. ::

    [libdefaults]
        rdns = false


For Developers
--------------

Instalation details
~~~~~~~~~~~~~~~~~~~

#. yum repository

   If you have installed PDC Server by some yum repository, PDC Client is in
   the same repository that you used.

   So to install PDC Client, just need to ::

    $ sudo yum install pdc-client -y

#. build from source

   If you have got the code and setup your development environment (see
   :ref:`development`), then you could build from source and install the
   client and it's dependency package python-pdc ::

    $ git checkout `{release-tag}`
    $ make rpm
    $ sudo yum install dist/noarch/python-pdc*.noarch.rpm dist/noarch/pdc-client*.noarch.rpm


General
~~~~~~~

The PDC Client (package name: pdc_client) is mainly build up with Python
`argparse` module and PDC's Python module `pdc_client`.

It is powered by `Beanbag <https://github.com/dmach/beanbag>`_, a simple module
that lets you access REST APIs in an easy way.
