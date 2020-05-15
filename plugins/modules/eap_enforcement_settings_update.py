#!/usr/bin/python
# -*- coding: utf-8 -*-
#


from __future__ import absolute_import, division, print_function
__metaclass__ = type
import os


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
        result = dict()
        self.subscription_id = self.module.params.get('subscription_id', None)
        self.subscription = self.client.getSubscriptionById(self.subscription_id)
        del self.subscription['configuration']['details']
        del self.subscription['cancel_time']
        self.subscription['configuration']["update_comment"] = "update configuration"

        high_risk_attack_mitigation = self.module.params.get('high_risk_attack_mitigation', None)

        print('#########')
        print(high_risk_attack_mitigation['enabled'])
        print('#########')

        if high_risk_attack_mitigation is not None:
            if high_risk_attack_mitigation['enabled'] is not None:
                self.subscription['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['enabled'] = high_risk_attack_mitigation['enabled']
            if high_risk_attack_mitigation['mode'] is not None:
                self.subscription['configuration']['waf_service']['policy']['high_risk_attack_mitigation']['enforcement_mode'] = high_risk_attack_mitigation['mode']

        malicious_ip = self.module.params.get('malicious_ip', None)
        if malicious_ip is not None:
            if malicious_ip['enabled'] is not None:
                self.subscription['configuration']['waf_service']['policy']['malicious_ip_enforcement']['enabled'] = malicious_ip['enabled']
            if malicious_ip['mode'] is not None:
                self.subscription['configuration']['waf_service']['policy']['malicious_ip_enforcement']['enforcement_mode'] = malicious_ip['mode']

        threat_campaign = self.module.params.get('threat_campaign', None)
        if threat_campaign is not None:
            if threat_campaign['enabled'] is not None:
                self.subscription['configuration']['waf_service']['policy']['threat_campaigns']['enabled'] = threat_campaign['enabled']
            if threat_campaign['mode'] is not None:
                self.subscription['configuration']['waf_service']['policy']['threat_campaigns']['enforcement_mode'] = threat_campaign['mode']

        self.uri = '/v1/svc-subscription/subscriptions/{0}'.format(self.subscription_id)
        response = self.client.put(self.uri, data = self.subscription)
        return response


enforcement_spec = {
    'enabled': dict(
        required=False,
        type='bool',
        default=None,
    ),
    'mode': dict(
        required=False,
        choices=['monitoring','blocking'],
        default=None,
    ),
}

privacy_spec = {
    'data_guard': dict(
        required=False,
        type='bool',
    ),
    'mask_credit_card': dict(
        required=False,
        type='bool',
    ),
    'mask_ssn': dict(
        required=False,
        type='bool',
    ),
    'masking': dict(
        required=False,
        type='bool',
    ),
}


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            subscription_id=dict(required=True),
            high_risk_attack_mitigation=dict(type='dict', options=enforcement_spec),
            malicious_ip=dict(type='dict', options=enforcement_spec),
            threat_campaign=dict(type='dict', options=enforcement_spec),
            compliance_privacy=dict(type='dict', options=privacy_spec),
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
        results=mm.exec_module()
        results['queried']=True
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))

if __name__ == '__main__':
    main()
