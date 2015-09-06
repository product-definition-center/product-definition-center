# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Red Hat
# Licensed under The MIT License (MIT)
# http://opensource.org/licenses/MIT
#
import beanbag
import requests
import requests_kerberos
import warnings
import json
from os.path import expanduser, isfile

import monkey_patch

monkey_patch.monkey_patch_kerberos()

settings = {
    "url": None,
    "token": None,
    "insecure": True,
    "develop": False,
    "comment": None,
}

GLOBAL_CONFIG_FILE = '/etc/pdc/client_config.json'
USER_SPECIFIC_CONFIG_FILE = expanduser('~/.config/pdc/client_config.json')
CONFIG_URL_KEY_NAME = 'host'
CONFIG_INSECURE_KEY_NAME = 'insecure'
CONFIG_DEVELOP_KEY_NAME = 'develop'
CONFIG_TOKEN_KEY_NAME = 'token'


def _read_file(file_path):
    data = {}
    if isfile(file_path):
        with open(file_path, 'r') as config_file:
            data = json.load(config_file)
    return data


def read_config_file(server_alias):
    result = _read_file(GLOBAL_CONFIG_FILE).get(server_alias, {})
    result.update(_read_file(USER_SPECIFIC_CONFIG_FILE).get(server_alias, {}))
    return result


def set_option(name, value):
    if name in settings:
        if value is not None:
            settings[name] = value
    else:
        raise KeyError("Invalid setting %s" % name)


def make_client():
    if not settings['url']:
        raise ValueError("Invalid pdc instance url.")
    return pdc_client(**settings)


def obtain_token(pdc):
    """
    Try to obtain token from all end-points that were ever used to serve the
    token. If the request returns 404 NOT FOUND, retry with older version of
    the URL.
    """
    token_end_points = ('token/obtain',
                        'obtain-token',
                        'obtain_token')
    for end_point in token_end_points:
        try:
            return pdc.auth[end_point]._()['token']
        except beanbag.BeanBagException, e:
            if e.response.status_code != 404:
                raise
    raise Exception('Could not obtain token from any known URL.')


def pdc_client(url, token=None, insecure=False, develop=False, debug=False, comment=None):
    session = requests.Session()

    if not develop:
        # For local environment, we don't need to require a token,
        # just access API directly.
        # REQUIRED, OPTIONAL, DISABLED
        session.auth = requests_kerberos.HTTPKerberosAuth(
            mutual_authentication=requests_kerberos.DISABLED)

    if insecure:
        # turn off for servers with insecure certificates
        session.verify = False

        # turn off warnings about making insecure calls
        if requests.__version__ < '2.4.0':
            print "Requests version is too old, please upgrade to 2.4.0 or latest."
            # disable all warnings, it had better to upgrade requests.
            warnings.filterwarnings("ignore")
        else:
            requests.packages.urllib3.disable_warnings()

    pdc = beanbag.BeanBag(url, session=session)

    if not develop:
        # For develop environment, we don't need to require a token
        if not token:
            token = obtain_token(pdc)
        session.headers["Authorization"] = "Token %s" % token

    if comment:
        session.headers["PDC-Change-Comment"] = comment

    return pdc, session
