.. _pdc_client:

PDC Client
==========

PDC Client(package name: pdc-client) is a shell CLI that make it easier to
manipulate data from PDC servers.

It's been shipped out with PDC Server(package name: pdc-server) since PDC v0.2.0-0.1.beta.


Installation
------------

#. yum repository

If you have installed PDC Server by some yum repository, PDC Client is in the
same repository that you used.

So to install PDC Client, just need to::

    $ sudo yum install pdc-client -y

#. build from source

If you have got the code and setup your development environment(see :ref:`development`),
then you could build from source and install the client and it's dependency package python-pdc::

    $ git checkout `{release-tag}`
    $ make rpm
    $ sudo yum install dist/noarch/python-pdc*.noarch.rpm dist/noarch/pdc-client*.noarch.rpm

#. configure server settings

If you want to customize server configuration, please edit the file '/etc/pdc/client_config.json' for
global configuration or create and edit '~/.config/pdc/client_config.json' for the current user specific
configuration. E.g.

    {
        "local": {
            "host": "http://localhost:8000/rest_api/v1/",
            "develop": true,
            "insecure": false
        },
        "prod": {
            "host": "https://pdc.example.com/rest_api/v1/",
            "token": xxxxxxxxxxxxx
        }
    }

Usage
-----

The help message is available via::

    $ pdc_client -h
    $ # or
    $ pdc_client --help

Known Issues
------------

Under enterprise intranet, `Reverse DNS mismatches <http://web.mit.edu/Kerberos/www/krb5-latest/doc/admin/princ_dns.html#reverse-dns-mismatches>`_
may cause problems when doing kerberos auth.

Once you found out that you could `kinit` but still can not authenticate yourself to pdc servers,
please check your krb5.conf and make sure that::

    [libdefaults]
        rdns = false

is there, and normally this will resolve your problem.

For Developers
--------------

The PDC Client(package name: pdc_client) is mainly build up with Python `optparser` module and PDC's
Python module `pdc_client`.

And the PDC Python module(package name: python-pdc) is powered by `Beanbag <https://github.com/dmach/beanbag>`_,
a simple module that lets you access REST APIs in an easy way.
