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
  REPOs: https://github.com/release-engineering/productmd.git
* patternfly1
  REPOs: https://copr.fedoraproject.org/coprs/patternfly/patternfly1/
* django-filter >= 0.9.2
* python-qpid-proton


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


Option 3: Start it on Docker
````````````````````````````````

* Install Docker: the link: https://docs.docker.com/installation/ will share the steps.
  If you can't install docker via the following command, please check the link in detail.
  ::
    $ sudo yum install docker-engine
  Then start the Docker daemon.
  ::
    $ sudo service docker start

* Use this to build a new image
  ::
    $ sudo docker build -t <YOUR_NAME>/pdc <the directory your Dockerfile is located>

* Running the container
  ::
    $ docker run -it -P -v $PWD:$PWD <YOUR_NAME>/pdc python $PWD/manage.py runserver 0.0.0.0:8000

* Check the addresses
   step1. Check the address of the docker machine
       127.0.0.1 --> DOCKER_HOST

   step2. Check the mapped port of your running container
   ::
       $ sudo docker ps -l --> PORTS

* Access it
 visit <DOCKER_HOST:PORTS> on your web browser


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
