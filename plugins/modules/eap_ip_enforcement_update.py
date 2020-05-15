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
  - Alex Shemyakin
'''

EXAMPLES = r'''
## TODO
## see example.yml
'''

RETURN = r'''
## TODO
'''

SUBSCRIPTION_BY_ID_URL = "/v1/svc-subscription/subscriptions/{0}"

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback

try:
    from ansible.module_utils.cloudservices import HttpRestApi, HttpConnection, F5ModuleError, f5_cs_argument_spec
except ImportError:
    from ansible_collections.ashemyakin.cloudservices.plugins.module_utils.cloudservices import HttpRestApi, HttpConnection, F5ModuleError, f5_cs_argument_spec

class ModuleManager(object):
    def __init__(self, *args, **kwargs):
        self.module = kwargs.pop('module', None)
        self.client = kwargs.pop('client', None)
        f5_cs = self.module.params.get('f5_cloudservices', None)
        self.username = f5_cs['user']
        self.password = f5_cs['password']
        self.client.login(self.username, self.password)

    def exec_module(self):
        self.subscription_id = self.module.params.get('subscription_id', None)
        self.ip_enforcement_list = self.module.params.get('ip_enforcement', None)
        self.subscription = self.client.getSubscriptionById(self.subscription_id)
        del self.subscription['configuration']['details']
        del self.subscription['cancel_time']
        self.subscription['configuration']["update_comment"] = "update configuration"
        self.subscription['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['ip_enforcement']['ips'] = self.ip_enforcement_list
        self.uri = SUBSCRIPTION_BY_ID_URL.format(self.subscription_id)
        self.response = self.client.put(self.uri, data = self.subscription)
        return self.response


ip_enforcement_spec = {
    'address': dict(
        required=True,
    ),
    'description': dict(
        required=True,
    ),
    'action': dict(
        required=True,
    ),
    'log': dict(
        required=True,
    )
}

class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            subscription_id=dict(required=True),
            ip_enforcement=dict(type='list', options=ip_enforcement_spec),
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
        mm = ModuleManager(module=module, client=HttpRestApi(HttpConnection()))
        results = mm.exec_module()
        results["changed"] = True
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))

if __name__ == '__main__':
    main()
