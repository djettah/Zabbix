#!/usr/bin/env python3
# -*- coding: utf-8 -*-


print ("testmod01 here")
"aaaaaaaaaaaaa"

def testfunc():
    print ("a=%s" % AVAR)

def get_zabbix_token(server, user, password):
    url = 'http://%s/zabbix/api_jsonrpc.php' % server
