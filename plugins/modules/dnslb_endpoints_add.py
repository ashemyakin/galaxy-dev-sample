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

import random
import string

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
        self.endpoint = self.module.params.get('endpoint', None)
        self.username = f5_cs['user']
        self.password = f5_cs['password']
        self.api_uri = f5_cs['api_uri']
        self.client = HttpRestApi(HttpConnection(self.api_uri))
        self.client.login(self.username, self.password)
        self.subscription = self.client.getSubscriptionById(self.subscription_id)

    def randomString(self, stringLength=4):
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for i in range(stringLength))

    def exec_module(self):
        self.parse_subscriptions = self.subscription['configuration']['gslb_service']['virtual_servers']
        if 'Id' in self.endpoint:
            endpoint_id='{}'.format(self.endpoint['Id'])
            self.endpoint.pop('Id')
        else:
            endpoint_id='ipEndpoint_{0}_{1}_{2}_{3}_{4}'.format(
                self.randomString(8),
                self.randomString(),
                self.randomString(),
                self.randomString(),
                self.randomString(12)
            )
        if self.endpoint['virtual_server_type'] == 'cloud':
            if 'vip_id' in self.endpoint: self.endpoint.pop('vip_id')
            if 'translation_address' in self.endpoint: self.endpoint.pop('translation_address')
        self.parse_subscriptions[endpoint_id] = self.endpoint
        self.uri = SUBSCRIPTION_BY_ID_URL.format(self.subscription_id)
        self.response = self.client.put(self.uri, data = self.subscription)
        return self.response
        # return self.subscription


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            subscription_id=dict(required=True),
            endpoint=dict(type='dict',
                Id=dict(required=False),
                virtual_server_type=dict(
                    required=True,
                    choices=['cloud','bigip-ltm']
                ),
                display_name=dict(required=True),
                port=dict(type='int', required=True),
                address=dict(required=True),
                monitor=dict(required=True),
                vip_id=dict(required=False),
                translation_address=dict(required=False),
            ),
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

