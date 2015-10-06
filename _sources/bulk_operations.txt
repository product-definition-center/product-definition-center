.. _bulk_operations:


Bulk operations
===============

The REST API provides a way to perform many operations in a single request.
However, all these operations in a single request must work with the same
collection (e.g. *release components* or *products*).

All these *bulk* operations are available on the resource list URL. Unless
stated otherwise in the documentation for a particular resource, the bulk
operation is implemented in terms of the standard call operating on a single
item.

The bulk call is atomic – all operations will be performed or none will.


Create
------

The input to this call should be a list of JSON objects. The rules for the
items in the list are same as when creating a single item in the collection.

The items will be created in the order in which they were specified in the
request.

The response from this call will include a list of whatever would be returned
by creating the resources one by one. The status code on success is ``201
CREATED``.

Note that the only way in which the bulk create differs from regular create is
the request data.


Delete
------

To delete multiple items in a collection, send a ``DELETE`` request to the list
URL. The request should include a body which should be a list of identifiers of
items to be deleted.

The items will be deleted in the order in which they were specified in the
request.

The exact format of the identifier is collection specific. Generally it should
be the identifier you would append to the URL to get a detail view of the item.

On success the response will be ``204 NO CONTENT``.


Update
------

Updating multiple items is possible via the ``PUT`` or ``PATCH`` method
directed to the list URL of a collection. In both cases, the request body
should be a JSON object, where keys are identifiers of objects (same as for
bulk delete) and their values describe desired changes.

Exact format of the changes description is resource dependant. It should have
the same structure as when updating a single item.

Because JSON objects are not ordered, the order in which the items will be
updated is not specified and can be different to what is specified in the
request.

On success the response will have the ``200 OK`` status code. The response body
will include a JSON object with the same structure as in the original request,
only change descriptions will be replaced with whatever gets returned by the
update method for single item. Note that if the requested change results in a
change of the identifier, the response will still contain the old identifier
with new value for the item.


Errors
------

If an error occurs during processing a bulk operation, all changes from the
request will be aborted and no change log will be recorded. The status code of
an error response depends on what went wrong.

The structure of the response body should (in case of client errors) consist of
a JSON object with the following structure.::

    {
        "detail":             <string|object>,
        "id_of_invalid_data": <string|int>,
        "invalid_data":       object
    }

The ``detail`` key denotes a more precise description of the error. Its value
is supplied by the single item manipulating function.

The ``id_of_invalid_data`` describes which part of the request caused the error.
For create, it is an integer index from the request array (starting from zero),
for update or delete it is the identifier.

The ``invalid_data`` contains the actual part of request that was invalid. It
is only present when creating or updating.

Please note that the processing always stops when encountering the first error.
It may be very well possible that even when the reported error is fixed, the
request will fail with another error.
