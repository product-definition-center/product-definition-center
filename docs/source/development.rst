.. _development:


Setup development environment
=============================


Source Code
-----------

::

    $ git clone https://github.com/release-engineering/product-definition-center.git


Installation
------------


Option 1: Start it on RPM
`````````````````````````

For development purposes, install following deps:

* python = 2.7
* python-django = 1.8.1
* python-ldap
* python-requests
* python-requests-kerberos
* python-mock
* kobo >= 0.4.2
* kobo-rpmlib
* kobo-django
* koji
* djangorestframework>=3.1
* django-mptt >= 0.7.1
* Markdown
* beanbag >= 1.9.2
* django-cors-headers
* productmd
* patternfly1

  REPOs: https://copr.fedoraproject.org/coprs/patternfly/patternfly1/
* django-filter >= 0.9.2


Option 2: Start it on virtualenv
````````````````````````````````

* Koji is not available on PyPI. You must install the `koji` package to your system via

  ::

    $ sudo yum install koji

  before creating a virtualenv.

* After that, run

  ::

    $ pip install virtualenvwrapper

  and setup according to 'Setup' steps in /usr/bin/virtualenvwrapper.sh. Then do with

  ::

    $ mkvirtualenv pdc --system-site-packages

  to include `koji` into your *pdc* virtualenv.

* run the following

  ::

    $ workon pdc
    $ pip install -r requirements/devel.txt

  to active *pdc* virtualenv and install all the deps.


Customize settings
------------------

You can use the dist settings template by copying it to `settings_local.py`::

    $ cp settings_local.py.dist settings_local.py

Feel free to customize your `settings_local.py`. Changes will be populated automatically. In local development environment,
you may need to set "DEBUG = True" and comment out " ALLOWED_HOSTS" setting, meanwhile uncomment 'REST_FRAMEWORK' section
but keep 'DEFAULT_PERMISSION_CLASSES' item commented.


Init DB
-------

To initialize database, run::

    $ python manage.py migrate --noinput


Run devel server
----------------

To run development server, run::

    $ make run

For development you may find it useful to enable Django Development Toolbar.

Related settings is documented in `devel settings` section in `settings_local.py.dist`.
