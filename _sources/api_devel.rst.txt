.. _api_devel:

API Development
===============

Each resource available on the REST API is implemented in terms of a couple
objects. The main one is a ``ViewSet``, which may optionally use a
``Serializer`` and a ``FilterSet``.

This is a guide for adding new resources.


Checklist
---------

#. Identify where to implement it: it can be part of existing application or
   you can create a new application. If you want a new application, use ::

    $ mkdir pdc/apps/your_app
    $ python manage.py startapp your_app pdc/apps/your_app

#. Create your models. Make sure to implement ``export`` method for each model
   that will be editable through the API.

#. Generate migrations ::

   $ python manage.py makemigrations your_app

#. Make sure the ``ViewSet`` inherits from ``StrictQueryParamMixin`` to
   properly handle unknown query parameters.

#. If the resource objects can be created, updated or deleted, use
   ``ChangeSet*`` mixins (or ``PDCModelViewSet`` as single parent).

#. The docstring of the methods will be visible in browsable documentation. Use
   Markdown for formatting. See below for other helpers you can use to simplify
   documentation.

#. Serializer should inherit from ``StrictSerializerMixin`` or implement the
   same logic itself (report error when unknown field is specified).

#. Write test cases for both success and error paths.


Writing documentation
---------------------

The browsable documentation is exported from docstrings of view set methods. It
uses `Markdown`_ as a markup language. There are a couple helpers that make
some things easier.

.. _markdown: http://daringfireball.net/projects/markdown/syntax

First of all, string ``%(HOST_NAME)s``, ``%(API_ROOT)s`` expand to host name of
the current server and path to the API root, respectively.

To include a link to another resource, rather than using the macros above,
there is a better way:

 * ``$URL:resourcename:param1$`` will expand to URL to that resource. Examples:

   * ``$URL:release-list$`` → ``http://pdc.example.com/rest_api/v1/releases/``
   * ``$URL:product-detail:dp$`` → ``http://pdc.example.com/rest_api/v1/products/dp/``

 * ``$LINK:resourcename:param1:param2$`` will expand to clickable link to that
   resource. The link label will be the URL of the resource (without the host
   name).

To describe available query filters, use ``%(FILTERS)s`` macro. This expands to
an unordered list with filter names and types of the value. The serializer can
be described with ``%(SERIALIZER)s``, which expands to a code block with JSON
describing the data. For create/update actions you may need to use
``%(WRITABLE_SERIALIZER)s`` which excludes all read-only fields.
