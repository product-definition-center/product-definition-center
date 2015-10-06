.. _using_api:

Using API
=========

This page contains details about using PDC from the API user view-point.


Authentication
--------------

By default, all the API calls require authentication. While the web UI is
authenticated using an external system such as Kerberos or SAML2, the API uses
a custom authentication for performance reasons.

The expected workflow is as follows:

1. Obtain an authorization token from the API ``/rest_api/v1/token/obtain/``.
   This is one of end-points that actually use the same authentication system
   as the web UI.

2. Perform requested actions using the token. It needs to be sent with the
   request in an HTTP header ``Authorization``. With ``curl``, this can be done
   with the ``-H`` flag (for example ``-H "Authorization: Token XXX"``).

The token you receive from the API is tied to your user account. Currently, the
token is valid indefinitely. However, if you leak it somewhere, you can
manually request a new token, which will invalidate the old one. To do this,
use the ``/rest_api/v1/token/refresh/`` API.

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
set up different size of a page. There is a special value of ``-1`` for the
page size, which would turn pagination off and give all the results at once. In
this case, the response is just the result array without any count or URLS.

Please be careful when turning the pagination off. If your query could return
hundreds or thousands of results, consider getting the page by page instead.


Change monitoring
-----------------

Whenever a change is performed through the API, a log is create so that it is
possible to find out what, when, why and by who was changed.

The changes can be viewed from the API under the ``/rest_api/v1/changesets/``
end-point. There is also a view on the web pages under ``/changes/``. Currently
there is no link to it.

To store the reason for the change, add HTTP header ``PDC-Change-Comment``,
whose value is an arbitrary string that will be stored with the change.
