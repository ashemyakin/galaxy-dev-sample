#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


#import datetime
#import json

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.module_utils.cloudservices import HttpRestApi
except ImportError:
    from ansible_collections.sample.f5_adns.plugins.module_utils.cloudservices import HttpRestApi


def main():
    api = HttpRestApi()
    print(api.time())


if __name__ == '__main__':
    main()
