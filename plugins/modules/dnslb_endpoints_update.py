#!/usr/bin/python
# -*- coding: utf-8 -*-
#


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
## TODO
author:
  - Ales Shemyakin
'''

EXAMPLES = r'''
## TODO
## see example.yml
'''

RETURN = r'''
## TODO
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from ansible.module_utils.cloudservices import HttpRestApi, HttpConnection, F5ModuleError, f5_cs_argument_spec
except ImportError:
    from ansible_collections.ashemyakin.cloudservices.plugins.module_utils.cloudservices import HttpRestApi, HttpConnection, F5ModuleError, f5_cs_argument_spec

SUBSCRIPTION_BY_ID_URL = "/v1/svc-subscription/subscriptions/{0}"

class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        f5_cs = self.module.params.get('f5_cloudservices', None)
        self.subscription_id = self.module.params.get('subscription_id', None)
        self.endpoints = self.module.params.get('endpoints', None)
        self.username = f5_cs['user']
        self.password = f5_cs['password']
        self.api_uri = f5_cs['api_uri']
        self.client = HttpRestApi(HttpConnection(self.api_uri))
        self.client.login(self.username, self.password)
        self.subscription = self.client.getSubscriptionById(self.subscription_id)

    def exec_module(self):
        self.parse_subscriptions = self.subscription['configuration']['gslb_service']['virtual_servers']
        self.parse_subscriptions.clear()
        for endpoint in self.endpoints:
            endpoint_id='{}'.format(endpoint['id'])
            endpoint.pop('id')
            self.parse_subscriptions[endpoint_id] = endpoint
        self.uri = SUBSCRIPTION_BY_ID_URL.format(self.subscription_id)
        self.response = self.client.put(self.uri, data = self.subscription)
        return self.response

endpoint_spec = {
    'id': dict(
        required=False,
    ),
    'virtual_server_type': dict(
        required=True,
    ),
    'display_name': dict(
        required=True,
    ),
    'port': dict(
        required=True,
    ),
    'address': dict(
        required=True,
    ),
    'monitor': dict(
        required=True,
    ),
    'vip_id': dict(
        required=False,
    ),
    'translation_address': dict(
        required=False,
    )
}

class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            subscription_id=dict(required=True),
            endpoints=dict(type='list', options=endpoint_spec),
        )
        self.argument_spec = {}
        self.argument_spec.update(f5_cs_argument_spec)
        self.argument_spec.update(argument_spec)

def main():
    spec = ArgumentSpec()

    module = AnsibleModule(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
    )

    try:
        mm = ModuleManager(module=module)
        results = mm.exec_module()
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))

if __name__ == '__main__':
    main()

