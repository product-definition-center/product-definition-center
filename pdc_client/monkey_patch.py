# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
from requests_kerberos.kerberos_ import log, _negotiate_value, HTTPKerberosAuth


def handle_401(self, response, **kwargs):
    """Handles 401's, attempts to use gssapi/kerberos authentication"""

    log.debug("handle_401(): Handling: 401")
    if _negotiate_value(response) is not None:
        _r = self.authenticate_user(response, **kwargs)
        if _r is response:
            log.debug("handle_401(): fail to authenticate, something wrong "
                      "with the client.")
            _r.raise_for_status()
        log.debug("handle_401(): returning {0}".format(_r))
        return _r
    else:
        log.debug("handle_401(): Kerberos is not supported")
        log.debug("handle_401(): returning {0}".format(response))
        return response


def authenticate_user(self, response, **kwargs):
    """Handles user authentication with gssapi/kerberos"""

    auth_header = self.generate_request_header(response)
    if auth_header is None:
        # GSS Failure, return existing response
        return response

    log.debug("authenticate_user(): Authorization header: {0}".format(
        auth_header))
    response.request.headers['Authorization'] = auth_header

    # Consume the content so we can reuse the connection for the next
    # request.
    response.content
    response.raw.release_conn()

    _r = response.connection.send(response.request, **kwargs)
    _r.history.append(response)

    log.debug("authenticate_user(): returning {0}".format(_r))
    return _r


def monkey_patch_kerberos():
    HTTPKerberosAuth.handle_401 = handle_401
    HTTPKerberosAuth.authenticate_user = authenticate_user
