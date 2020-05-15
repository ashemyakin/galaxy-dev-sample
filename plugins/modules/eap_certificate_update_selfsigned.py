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
        self.account_id = self.subscription['account_id']
        self.fqdn = self.subscription['configuration']['details']['fqdn']
        self.https_port = self.module.params.get('https_port', 443)
        self.https_redirect = self.module.params.get('https_redirect', False)

        self.key_path = './{0}.key'.format(self.fqdn)
        self.cert_path = './{0}.cert'.format(self.fqdn)

        os.system('openssl genrsa -out {0} 2048'.format(self.key_path))
        os.system('openssl req -new -x509 -key {0} -out {1} -days 3650 -subj /CN={2}'.format(self.key_path, self.cert_path, self.fqdn))
        self.private_key = open(self.key_path, 'r').read()
        self.cert = open(self.cert_path, 'r').read()

        certificate_payload = dict(
            account_id=self.account_id,
            certificate=self.cert,
            private_key=self.private_key,
            passphrase='',
            certificate_chain='',
        )

        cert_response = self.client.post('/v1/svc-certificates/certificates', data=certificate_payload)
        self.certificate_id = cert_response['contents']['id']

        del self.subscription['configuration']['details']
        del self.subscription['cancel_time']
        self.subscription['configuration']["update_comment"] = 'update configuration'
        self.subscription['configuration']['waf_service']['application']['http']['https_redirect'] = self.https_redirect
        self.subscription['configuration']['waf_service']['application']['https'] = dict(
            enabled=True,
            port=self.https_port,
            tls=dict(certificate_id = self.certificate_id),
        )

        update_response = self.client.put('/v1/svc-subscription/subscriptions/{0}'.format(self.subscription_id), data = self.subscription)

        result = dict(
            certificate_id=self.certificate_id,
            fqdn=self.fqdn,
            subscription_id=self.subscription_id,
            account_id=self.account_id,
            cert=self.cert_path,
            key=self.key_path,
        )

        return result

class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        argument_spec = dict(
            subscription_id=dict(required=True),
            https_port=dict(required=False,type='int', default=443),
            https_redirect=dict(required=False, type='bool', default=False),
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
        results['changed']=True
        module.exit_json(**results)
    except F5ModuleError as ex:
        module.fail_json(msg=str(ex))

if __name__ == '__main__':
    main()
