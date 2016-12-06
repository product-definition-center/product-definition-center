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

For development purposes, install following dependencies:

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
  REPOs: https://github.com/release-engineering/productmd.git
* patternfly1
  REPOs: https://copr.fedoraproject.org/coprs/patternfly/patternfly1/
* django-filter >= 0.9.2
* python-qpid-proton


Option 2: Start it on virtualenv
````````````````````````````````

* Koji is not available on PyPI. You must install the `koji` package to your
  system via ``yum`` before creating a virtualenv. ::

    $ sudo yum install koji

* After that, run ::

    $ pip install virtualenvwrapper

  and setup according to 'Setup' steps in ``/usr/bin/virtualenvwrapper.sh``.
  Then run ::

    $ mkvirtualenv pdc --system-site-packages

  to include `koji` into your *pdc* virtualenv.

* Run the following ::

    $ workon pdc
    $ pip install -r requirements/devel.txt

  to activate *pdc* virtualenv and install all the dependencies.


Option 3: Start it on Docker
````````````````````````````

* Install Docker: see the `official installation
  guide <https://docs.docker.com/installation/>`_ for details. Generally, it
  might be enough to run install it with ``yum`` and the run it. ::

    $ sudo yum install docker-engine
    $ sudo service docker start

* Use this command to build a new image ::

    $ sudo docker build -t <YOUR_NAME>/pdc <the directory your Dockerfile is located>

* Run the container ::

    $ docker run -it -P -v $PWD:$PWD <YOUR_NAME>/pdc python $PWD/manage.py runserver 0.0.0.0:8000

* Check the address

  #. Find the address of the docker machine (127.0.0.1 --> DOCKER_HOST).

  #. Find the mapped port of your running container ::

       $ sudo docker ps -l --> PORT

* Access it by visiting ``DOCKER_HOST:PORT`` in your web browser.


Customize settings
------------------

You can use the dist settings template by copying it to `settings_local.py`::

    $ cp settings_local.py.dist settings_local.py

Feel free to customize your `settings_local.py`. Changes will be populated
automatically. In local development environment, you may need to set ``DEBUG =
True`` to get better error messages and comment out ``ALLOWED_HOSTS`` setting.

For development you might also consider uncommenting ``REST_FRAMEWORK`` section
but keeping nested ``DEFAULT_PERMISSION_CLASSES`` item commented. This will
disable authentication.


Init database
-------------

To initialize database, run::

    $ python manage.py migrate --noinput


Run devel server
----------------

To run development server, run::

    $ make run

For development you may find it useful to enable `Django Debug Toolbar
<http://django-debug-toolbar.readthedocs.org/en/1.3.2/>`_.

Related settings is documented in comment at the top of
``settings_local.py.dist``.
