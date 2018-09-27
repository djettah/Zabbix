#!/usr/bin/env python3

import requests
import sys
import argparse
import os
import json
sys.path.append(os.path.join(sys.path[0], 'lib'))
import debug_toolkit
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)



class OCUM_API(object):
    """docstring for OCUM_API"""
    def __init__(self, address, username, password):
        super(OCUM_API, self).__init__()
        self.address = address
        self.creds = (username, password)
        self.endpoint      = 'https://%s/rest/' % self.address
        self.headers      = {"Accept": "application/vnd.netapp.object.inventory.hal+json"}


    #def aggregates(self, query=None, search=None, sort=None, filter=None):
    def aggregates(self, params=None, discovery=False):
        rest_method = sys._getframe().f_code.co_name
        response = requests.get (url=self.endpoint + rest_method, params=params, headers=self.headers, timeout=30, auth=self.creds, verify=False)
        
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

                output = json.dumps({'data': data})

            return output

        else:
            print('[error] Incorrect response ({}):\n{}'.format(response.status_code, response.text))
            return False
            #exit()
    


def get_aggregates(url, headers, timeout, auth, query, search, sort, filter):
    response = requests.get (url=url, headers=headers, timeout=30, auth=auth, verify=False)
    #print(response)
    if response and '_embedded' in response.json().keys():
        return response.json()['_embedded']['netapp:aggregateInventoryList']

    else:
        print('[error] Incorrect response ({}):\n{}'.format(response.status_code, response.text))
        exit()


    

def get_aggregates_discovery(aggregates):
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
    return json.dumps(output)


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

    args = parser.parse_args()


    DEBUG               = debug_toolkit.DEBUG = debug_toolkit.TRACE = args.debug
    DRYRUN              = debug_toolkit.DRYRUN = args.dry_run
    
    OCUM_SERVER       = args.ocum_addr
    OCUM_USER         = args.ocum_user
    OCUM_PASSWORD     = args.ocum_pass
    OCUM_API_URL      = 'https://%s/rest/' % OCUM_SERVER
    OCUM_HEADERS      = {"Accept": "application/vnd.netapp.object.inventory.hal+json"}

    ocum = OCUM_API(OCUM_SERVER, OCUM_USER, OCUM_PASSWORD)
    if args.query == 'aggregates':  
        result = ocum.aggregates(params = {'nodeId': 8}, discovery = args.discovery)
        if result: print(result)


if __name__ == "__main__":
    main()
