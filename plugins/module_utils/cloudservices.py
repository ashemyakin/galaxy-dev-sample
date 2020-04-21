#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import datetime
import json

class HttpRestApi():
    def __init__(self):
        pass

    def time(self):
        date = str(datetime.datetime.now())
        return(json.dumps({
        "time" : date
        }))

