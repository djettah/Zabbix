#!/usr/bin/env python3

import requests
import sys
import argparse
import os
import json
import logging

sys.path.append(os.path.join(sys.path[0], 'lib'))
import debug_toolkit
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class OCUM_API(object):
    """NetApp OCUM API client"""
    def __init__(self, address, creds):
        super(OCUM_API, self).__init__()
        self.address    = address
        self.creds      = creds
        self.api_uri    = 'https://%s/rest/' % self.address
        self.headers    = {"Accept": "application/vnd.netapp.object.inventory.hal+json"}

    def items(self, item_type, params=None, discovery=None):
        resource = item_type + "s"
        resource_uri = self.api_uri + resource
        response = requests.get (url=resource_uri, params=params, headers=self.headers, timeout=30, auth=self.creds, verify=False)
        output = []
        if response:
            if '_embedded' in response.json().keys():
                output = response.json()['_embedded']['netapp:{}InventoryList'.format(item_type)]

            if discovery:
                data = []
                

                for item in output:
                    discovery_item = []
                    common_items = {
                            '{#CLUS_NAME}'   : item['cluster']['label'],
                            '{#CLUS_ID}'     : item['cluster']['id'],
                            '{#STATUS}'      : item['status']
                    }

                    if item_type == "aggregate":
                        discovery_item = {
                            '{#AGGR_NAME}'   : item[item_type]['label'],
                            '{#AGGR_ID}'     : item[item_type]['id'],
                            '{#NODE_NAME}'   : item['node']['label'],
                            '{#NODE_ID}'     : item['node']['id'],
                            **common_items
                        }

                    if item_type == "svm":
                        discovery_item = {
                            '{#SVM_NAME}'   : item[item_type]['label'],
                            '{#SVM_ID}'     : item[item_type]['id'],
                            **common_items
                        }

                    if item_type == "volume":
                        discovery_item = {
                            '{#VOL_NAME}'   : item[item_type]['label'],
                            '{#VOL_ID}'     : item[item_type]['id'],
                            **common_items
                        }


                    if discovery_item: data.append(discovery_item)

                output = {'data': data}

        else:
            logging.error('Incorrect response ({}):\n{}'.format(response.status_code, response.text))

        return output

    # def volume(self, params=None, discovery=False):
    #     item_type = sys._getframe().f_code.co_name
    #     items = self.items(item_type=item_type, params=params)
    #     return items
    

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--ocum-addr", help="OCUM server address")
    parser.add_argument("--ocum-user", help="OCUM account login")
    parser.add_argument("--ocum-pass", help="OCUM account password")
    parser.add_argument("--dry-run", action="store_true", help="dry run mode")
    parser.add_argument("-d", "--debug", action="store_true", help="debug mode")
    parser.add_argument("--trace", action="store_true", help="trace mode")
    parser.add_argument("--query", help="Query type: <aggregate|volume|etc>")
    parser.add_argument("--discovery", action="store_true", help="Output in Zabbix Discovery format")
    parser.add_argument("--params", help="Query params (json)")

    args = parser.parse_args()

    DEBUG               = debug_toolkit.DEBUG = debug_toolkit.TRACE = args.debug
    DRYRUN              = debug_toolkit.DRYRUN = args.dry_run
    
    OCUM_ADDR           = args.ocum_addr
    OCUM_CRED           = (args.ocum_user, args.ocum_pass)

    ocum = OCUM_API(OCUM_ADDR, OCUM_CRED)
    
    params = None   #{'nodeId': 8}
    if args.params:
        try:
            params = json.loads(args.params)
        except:
            logging.warning("params invalid: {}".format(args.params))

    items = ocum.items(item_type=args.query, params=params, discovery=args.discovery)
    result = json.dumps(items)
    #result = getattr(ocum, args.query)(params = params, discovery = args.discovery)
    if result: print(result)

if __name__ == "__main__":
    main()
