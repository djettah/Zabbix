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


    #def aggregates(self, query=None, search=None, sort=None, filter=None):
    def aggregates(self, params=None, discovery=False):
        resource = sys._getframe().f_code.co_name
        resource_uri = self.api_uri + resource
        response = requests.get (url=resource_uri, params=params, headers=self.headers, timeout=30, auth=self.creds, verify=False)
        
        if response and '_embedded' in response.json().keys():
            output = aggregates = response.json()['_embedded']['netapp:aggregateInventoryList']

            if discovery:
                data = []
        
                for aggr in aggregates:
                    data.append( {
                            '{#AGGR_NAME}'   : aggr['aggregate']['label'],
                            '{#AGGR_ID}'     : aggr['aggregate']['id'],
                            '{#NODE_NAME}'   : aggr['node']['label'],
                            '{#NODE_ID}'     : aggr['node']['id'],
                            '{#CLUS_NAME}'   : aggr['cluster']['label'],
                            '{#CLUS_ID}'     : aggr['cluster']['id'],
                            '{#STATUS}'      : aggr['status']

                        })

                output = {'data': data}

            return output

        else:
            logging.error('Incorrect response ({}):\n{}'.format(response.status_code, response.text))
            return False
            #exit()
    
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--ocum-addr", help="OCUM server address")
    parser.add_argument("--ocum-user", help="OCUM account login")
    parser.add_argument("--ocum-pass", help="OCUM account password")
    parser.add_argument("--dry-run", action="store_true", help="turns on dry run mode (doesn't modify data)")
    parser.add_argument("-d", "--debug", action="store_true", help="turns on debug mode")
    parser.add_argument("--trace", action="store_true", help="turns on trace mode")
    parser.add_argument("--query", help="Query type: <aggregates|volumes>")
    parser.add_argument("--discovery", action="store_true", help="Discovery mode")
    parser.add_argument("--params", help="Query params (json)")

    args = parser.parse_args()

    DEBUG               = debug_toolkit.DEBUG = debug_toolkit.TRACE = args.debug
    DRYRUN              = debug_toolkit.DRYRUN = args.dry_run
    
    OCUM_ADDR           = args.ocum_addr
    OCUM_CREDS          = (args.ocum_user, args.ocum_pass)

    ocum = OCUM_API(OCUM_ADDR, OCUM_CREDS)
     
    
    try:
        params = json.loads(args.params)
    except:
        params = None   #{'nodeId': 8}
        logging.warning("params invalid: {}".format(args.params))

    result = getattr(ocum, args.query)(params = params, discovery = args.discovery)
    result = json.dumps(result)
    if result: print(result)


if __name__ == "__main__":
    main()
