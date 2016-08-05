.. _using_api:

Using API
=========

This page contains details about using PDC from the API user view-point.

PDC API Stability Promise
-------------------------

Product Definition Center promises API stability and forwards-compatibility of
APIv1 from version 0.9.0. In a nutshell, this means that code you develop
against PDC  will continue to work with future releases. You might be required
to make changes to your usage of the API when changing to a different version of
the API or when you want to make use of new features.


What *stable* means?
~~~~~~~~~~~~~~~~~~~~

In this context, stable means:
 * The documented APIs will not be removed or renamed
 * Arguments for APIs will not be removed or renamed
 * Keys in returned JSON dictionaries will not be removed or renamed
 * If new features are added to these APIs – which is quite possible – they will not break or change the meaning of existing methods. In other words, “stable” does not (necessarily) mean *complete*
 * Default values of optional arguments will not change
 * Order of returned results will not change for following results:
    * releases in releases resource API
    * composes inside compose_set in releases resource API
    * composes in composes resource API
 * If, for some reason, an API declared stable must be removed or replaced, it will be declared deprecated in given version of the API and removed/replaced in future version of API
 * We’ll only break backwards compatibility of these APIs if a bug or security hole makes it completely unavoidable.

To make use of this stability your client code has to accept unknown keys and
values in responses and ignore them if they are not recognized.

Exceptions
~~~~~~~~~~
There are a few exceptions to the above stability promise. Specifically:
 * APIs marked as *experimental* are not part of promise. This enables us to
   add new APIs and test them properly before marking them as stable
 * If a security or other high-impact bug is encountered we might break stability
   promise. This would be used as last resort. 

Authentication
--------------

By default, all the API calls require authentication. While the web UI is
authenticated using an external system such as Kerberos or SAML2, the API uses
a custom authentication for performance reasons.

The expected workflow is as follows:

1. Obtain an authorization token from the API ``/rest_api/v1/auth/token/obtain/``.
   This is one of end-points that actually use the same authentication system
   as the web UI.

2. Perform requested actions using the token. It needs to be sent with the
   request in an HTTP header ``Authorization``. With ``curl``, this can be done
   with the ``-H`` flag (for example ``-H "Authorization: Token XXX"``).

The token you receive from the API is tied to your user account. Currently, the
token is valid indefinitely. However, if you leak it somewhere, you can
manually request a new token, which will invalidate the old one. To do this,
use the ``/rest_api/v1/auth/token/refresh/`` API.

If you access the API through one of PDC client, the authentication can be
handled transparently for you.


Paging
------

The lists returned from the API can be quite long. They are paginated by
default with pages containing 20 items.

The structure of paginated reply is JSON object with following keys:

``count``
    Total number of items. Essentially, this tells you how many items you would
    get if you got all the pages and concatenated them.

``next``
    URL where you can get the next page. Contains ``null`` on the last page.

``previous``
    URL where the previous page is. On the first page it contains ``null``.

``results``
    The actual data as a JSON array.

You can control the details of the paginating by a couple query parameters. The
``page`` parameter specifies which page you want. With ``page_size`` you can
set up different size of a page. The maximum allowed number of results per page
is 100. Specifying anything higher has the same result as specifying 100. There
is a special value of ``-1`` for the page size, which would turn pagination off
and give all the results at once. In this case, the response is just the result
array without any count or URLS.

Please be careful when turning the pagination off. If your query could return
hundreds or thousands of results, consider getting the data page by page
instead.


Change monitoring
-----------------

Whenever a change is performed through the API, a log is created so that it is
possible to find out what, when, why and by who was changed.

The changes can be viewed from the API under the ``/rest_api/v1/changesets/``
end-point. There is also a view on the web pages. A logged-in user can access
it from the menu in top right corner.

To store the reason for the change, add HTTP header ``PDC-Change-Comment``,
whose value is an arbitrary string that will be stored with the change.


Override Ordering
-----------------

The client can override the ordering of the results with query parameter.
By default, the query parameter is named ``ordering``.
For example, to order releases by release_id:

http://example.com/rest_api/v1/releases/?ordering=release_id

The client may also specify reverse orderings by prefixing the field name with '-'.

For example, to reverse orderings of releases by release_id:

http://example.com/rest_api/v1/releases/?ordering=-release_id

