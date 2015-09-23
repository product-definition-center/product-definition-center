.. _deployment:


Deployment
==========


Install via yum
---------------

::

    $ yum install pdc-server

The RPM includes a cron job to perform daily synchronization of users with
LDAP. It is installed to ``/etc/cron.daily`` and does not need any
configuration.


Configure Django settings
-------------------------

::

    # mv settings_local.py.dist to settings_local.py
    # change database settings in /usr/lib/pythonX.Y/site-packages/pdc/settings_local.py


Initialize database
-------------------

::

    # create database
    $ su - postgres
    $ psql
    postgres=# create database "db_name" owner "user_name";
    postgres=# \q

    # migrate database
    $ django-admin migrate --settings=pdc.settings --noinput


Collect static
--------------

::

    $ django-admin collectstatic --settings=pdc.settings


Config apache
-------------

replace ``PDC_HOSTNAME`` with server's hostname in ``/etc/httpd/conf.d/pdc.conf``
