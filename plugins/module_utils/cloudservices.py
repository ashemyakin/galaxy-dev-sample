#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2020, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = """
---
author: Alex Shemyakin
short_description: HttpApi Plugin for F5 Cloud Services
description:
  - This HttpApi plugin provides methods to connect to F5 Cloud Services over a HTTP(S)-based api.
version_added: "1.0"
"""

import re

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.urls import Request
from ansible.module_utils.basic import env_fallback


try:
    import json
except ImportError:
    import simplejson as json


f5_cs_spec = {
    'user': dict(
        required=True,
        no_log=True,
        fallback=(env_fallback, ['F5_USER'])
    ),
   'password': dict(
        required=True,
        no_log=True,
        aliases=['pass', 'pwd'],
        fallback=(env_fallback, ['F5_PASSWORD']),
    ),
}

f5_cs_argument_spec = {
    'f5_cloudservices': dict(type='dict', options=f5_cs_spec),
}

BASE_HEADERS = {'Content-Type': 'application/json'}
LOGIN_URL = "/v1/svc-auth/login"
LOGOUT_URL = "/v1/svc-auth/logout"
RELOG_URL = "/v1/svc-auth/relogin"
SUBSCRIPTION_BY_ID_URL = "/v1/svc-subscription/subscriptions/{0}"


class HttpRestApi():
    def __init__(self, connection):
        self.connection = connection
        self.access_token = None
        self.refresh_token = None
        self.token_timeout = None

    def login(self, username, password):
        if username and password:
            payload = {
                'username': username,
                'password': password
                }
            response = self.send_request(LOGIN_URL, method='POST', data=payload, headers=BASE_HEADERS)
        else:
            raise AnsibleConnectionFailure('Username and password are required for login.')

        try:
            self.refresh_token = response['contents']['refresh_token']
            self.access_token = response['contents']['access_token']
            self.token_timeout = int(response['contents']['expires_at'])
            self.connection._auth = {'Authorization': 'Bearer {0}'.format(self.access_token)}
        except KeyError:
            raise ConnectionError('Server returned invalid response during connection authentication.')

    def getSubscriptionById(self, subscription_id):
        if subscription_id:
            response = self.send_request(SUBSCRIPTION_BY_ID_URL.format(subscription_id), method='GET', headers=BASE_HEADERS)
            return response['contents']
        else:
            raise AnsibleConnectionFailure('Subscription Id is required.')


    def _refresh_token(self, username):
        payload = {
            'username': username,
            'refresh_token': self.refresh_token
        }

        response = self.send_request(RELOG_URL, method='POST', data=payload, headers=BASE_HEADERS)
        try:
            self.access_token = response['contents']['access_token']
            # self.connection._auth = {'Authorization': 'Bearer %s' % self.access_token}
        except KeyError:
            raise ConnectionError('Server returned invalid response during connection authentication.')

    def handle_httperror(self, exc):
        err_5xx = r'^5\d{2}$'
        # We raise AnsibleConnectionFailure without passing to the module, as 50x type errors indicate a problem
        # with the service, anything else will be handled by the caller

        handled_error = re.search(err_5xx, str(exc.code))
        if handled_error:
            raise AnsibleConnectionFailure('Could not connect to {0}: {1}'.format(exc.reason))
        return False

    def send_request(self, url, method=None, **kwargs):
        body = kwargs.pop('data', None)
        data = json.dumps(body) if body else None
        self._display_request(method=method, data=data)

        try:
            response = self.connection.send(url, data, method=method, **kwargs)
            if response.getcode() in [200]:
                return dict(code=response.getcode(), contents=json.loads(response.read() or 'null'))
            else:
                raise ConnectionError('Request failed with status code {0}: {1}'.format(response.getcode(), response.read()))
        except HTTPError as exc:
            raise ConnectionError('Request failed with status code {0}: {1}'.format(exc.code, exc.reason))

    def _display_request(self, method, data):
         self.connection._log_messages(
            'F5 Cloud Services API Call: {0} with data {1}'.format(method, data)
         )

    def delete(self, url, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='DELETE', headers=headers, **kwargs)
        return self.send_request(url, method='DELETE', headers=BASE_HEADERS,  **kwargs)

    def get(self, url, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='GET', headers=headers, **kwargs)
        return self.send_request(url, method='GET', headers=BASE_HEADERS, **kwargs)

    def patch(self, url, data=None, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='PATCH', data=data, headers=headers, **kwargs)
        return self.send_request(url, method='PATCH', data=data, headers=BASE_HEADERS, **kwargs)

    def post(self, url, data=None, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='POST', data=data, headers=headers, **kwargs)
        return self.send_request(url, method='POST', data=data, headers=BASE_HEADERS, **kwargs)

    def put(self, url, data=None, account_id=None, **kwargs):
        if account_id:
            headers = {'X-F5aaS-Preferred-Account-Id': account_id}
            headers.update(BASE_HEADERS)
            return self.send_request(url, method='PUT', data=data, headers=headers, **kwargs)
        return self.send_request(url, method='PUT', data=data, headers=BASE_HEADERS, **kwargs)

class HttpConnection(object):
    def __init__(self):
        self._auth=None
        self.api_uri='api.cloudservices.f5.com'

    def _log_messages(self, message):
        return True

    def send(self, url, data, method="GET", **kwargs):
        headers=None
        use_proxy=True
        force=False
        timeout=120
        validate_certs=kwargs.pop('validate_certs', True)
        url_username=None
        url_password=None
        http_agent=None
        force_basic_auth=False
        follow_redirects='urllib2'
        client_cert=None
        client_key=None
        cookies=None
        headers = kwargs.pop('headers', None)

        self.request = Request(
            headers=headers,
            use_proxy=use_proxy,
            force=force,
            timeout=timeout,
            validate_certs=validate_certs,
            url_username=url_username,
            url_password=url_password,
            http_agent=http_agent,
            force_basic_auth=force_basic_auth,
            follow_redirects=follow_redirects,
            client_cert=client_cert,
            client_key=client_key,
            cookies=cookies
        )

        if data:
            kwargs['data'] = data

        if self._auth:
            self.request.headers['Authorization'] = self._auth['Authorization']

        self.request.headers['Content-Type'] = 'application/json'
        response = self.request.open(method, 'https://{0}{1}'.format(self.api_uri, url), **kwargs)
        return response

class F5ModuleError(Exception):
    pass

