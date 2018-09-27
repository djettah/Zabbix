#!/usr/bin/env python3

import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
import json
from zabbix.api import ZabbixAPI
from subprocess import Popen, PIPE, STDOUT

import debug_toolkit
from debug_toolkit import deflogger, dry_request



HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

@deflogger
def get_token(server, user, password, DRYRUN=False):
    url = 'https://%s/zabbix/api_jsonrpc.php' % server
    payload = dict(jsonrpc='2.0',
                         method='user.login',
                         params=dict(user=user,
                                     password=password),
                         id=1)
    headers = {'content-type': 'application/json', 'cache-control': 'no-cache'}
    req_dict = {'url':url, 'headers':headers, 'data':json.dumps(payload)}

    if debug_toolkit.DRYRUN and DRYRUN: 
        dry_request(url=url, headers=headers, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if 'result' in response.json().keys():
            return response.json()['result']
        else:
            print('Error! Incorrect response from get_token.')
            exit() 

def get_session_api(server, user, password):
    session = ZabbixAPI(url='https://{}/zabbix'.format(server), user=user, password=password)
    return session


@deflogger
def create_hostgroups(new_groups, token, server):
    url = 'https://%s/zabbix/api_jsonrpc.php' % server
    payload = dict(jsonrpc='2.0',
                   method='hostgroup.create',
                   params=dict(name=''),
                   auth=token,
                   id=1)
    
    for group in new_groups:
        payload['params']['name'] = group

        if debug_toolkit.DRYRUN: 
            dry_request(url=url, headers=HEADERS, payload=payload)
        else:
            response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)
            if "error" in response.json():
                print("Error while creating group ", group)
            else:
                print("The group", group, "has been created.")

@deflogger
def create_hosts(token, server, new_hosts, groupids, export_group):
    url = 'https://%s/zabbix/api_jsonrpc.php' % server    
    payload = dict(jsonrpc='2.0',
                   method='host.create',
                   auth=token,
                   id=1,
                   params=dict(name='',
                               host='',
                               templates=[],
                               groups=[dict(groupid='')],
                               inventory_mode=0,
                               interfaces=[dict(type=None,
                                                main=1,
                                                useip=1,
                                                ip='',
                                                dns='',
                                                port='161')],
                               inventory=dict(alias='')))
    
    for nh in new_hosts:
        payload['params']['groups'] = [dict(groupid='')]
        #if 'templates' in payload['params']:
        payload['params']['templates'] = []

        payload["params"]["name"] = nh["name"]["value"]
        payload["params"]["host"] = nh["name"]["value"] + "_" + nh["sys_id"]["value"]
        
        #if nh['x_itgra_monitoring_zabbix_template']:

        payload['params']['templates'] = [{'templateid': number} for number in nh['x_itgra_monitoring_zabbix_template']["value"]]
        
        payload['params']['inventory']['alias'] = nh['sys_id']["value"]

        payload['params']['inventory']['location_lat'] = nh['latitude']["value"]
        payload['params']['inventory']['location_lon'] = nh['longitude']["value"]


        # Determine which proxy to use by domain name (just hard code proxy id)
        # if 'sn.vcloud.kz' in nh["fqdn"] or 'sn.vcloud.kz' in nh["name"]:
        if nh['x_itgra_monitoring_zabbix_proxy']["value"]: payload['params']['proxy_hostid'] = nh['x_itgra_monitoring_zabbix_proxy']["value"]

        payload['params']['groups'][0]['groupid'] = groupids[nh['sys_class_name']["display_value"]]
        payload['params']['groups'].append(dict(groupid=export_group))
        payload['params']['interfaces'][0]['ip'] = nh['ip_address']["value"]
        payload["params"]["interfaces"][0]["dns"] = nh["fqdn"]["value"]
        
        if nh["sys_class_name"]["display_value"] == "Linux Server" or nh["sys_class_name"]["display_value"] == "Windows Server":
            payload["params"]["interfaces"][0]["type"] = 1
        else:
            payload["params"]["interfaces"][0]["type"] = 2


        if debug_toolkit.DRYRUN: 
            dry_request(url=url, headers=HEADERS, payload=payload)
        else:
            response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

            if 'error' in response.json():
                print('\nError while creating host "%s"\n' % nh['name'], response.json())
            else:
                print('Создан новый узел %s' % payload["params"]["name"])
            
    print('\nПроцедура синхронизации новых хостов завершена\n')

@deflogger
def get_hostgroups_by_name(token, host, name, DRYRUN=False):
    url = 'https://%s/zabbix/api_jsonrpc.php' % host
    payload = dict(jsonrpc='2.0',
                         method='hostgroup.get',
                         params=dict(output=['groupid', 'name'],
                                     search=dict(name=name)),
                         auth=token,
                         id=1)

    if debug_toolkit.DRYRUN and DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)
        if 'result' in response.json().keys():
            return response.json()['result']
        else:
            print('Error! Incorrect response from get_servicenow_groups_from_zabbix.')
            exit()

@deflogger
def get_hostgroups(token, host, DRYRUN=False):
    url = 'https://%s/zabbix/api_jsonrpc.php' % host
    payload = dict(jsonrpc='2.0',
                         method='hostgroup.get',
                         params=dict(output=['groupid', 'name']),
                         auth=token,
                         id=1)
    if debug_toolkit.DRYRUN and DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)
        if 'result' in response.json().keys():
            return response.json()['result']
        else:
            print('Error! Incorrect response from get_servicenow_groups_from_zabbix.')
            exit()

@deflogger
def get_hosts_by_groupids(token, host, ids, DRYRUN=False):
    url = 'https://%s/zabbix/api_jsonrpc.php' % host
    payload = dict(jsonrpc='2.0',
                        method='host.get',
                        params=dict(output=['name', 'host'],
                                    selectInventory=["alias","location","location_lon","location_lat"],
                                    selectGroups=["groupid", "name"],
                                    selectParentTemplates=["templateid"],
                                    selectInterfaces=["ip", "interfaceid", "dns", "type"],
                                    groupids=ids),
                        id=1,
                        auth=token)



    if debug_toolkit.DRYRUN and DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if 'result' in response.json().keys():
            return response.json()['result']
        else:
            print('Error! Incorrect response from get_hosts_by_ids.')
            exit()
@deflogger
def get_hosts(token, host, DRYRUN=False):
    url = 'https://%s/zabbix/api_jsonrpc.php' % host
    payload = dict(jsonrpc='2.0',
                        method='host.get',
                        params=dict(output=['name', 'host'],
                                    selectInventory=["alias"],
                                    selectGroups=["groupid", "name"],
                                    selectParentTemplates=["templateid"],
                                    selectInterfaces=["ip", "interfaceid", "dns", "type"]
                                    ),
                        id=1,
                        auth=token)


    if debug_toolkit.DRYRUN and DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if 'result' in response.json().keys():
            return response.json()['result']
        else:
            print('Error! Incorrect response from get_hosts_by_ids.')
            exit()

@deflogger
def get_items(token, host, item_type, output="extend", DRYRUN=False):
    """ex-get-templates & get-proxies"""
    url = 'https://%s/zabbix/api_jsonrpc.php' % host
    params = {
                    "output": output #,
                    #"selectInterface": "extend"
                }
    

    if item_type == 'host':
        params['selectInventory'] = ["location", "location_lon", "location_lat"]
        params['selectParentTemplates'] = ["host","name"]
        params['selectGroups'] = ["groupid"]

    payload = {
                "jsonrpc": "2.0",
                "method": item_type + ".get",
                "params": params,
                "auth": token,
                "id": 1
            }

    if debug_toolkit.DRYRUN and DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if 'result' in response.json().keys():
            return response.json()['result']
        else:
            print('Error! Incorrect response from get_items.\n' + response.json()['result'])
            exit()

@deflogger
def get_templates_api(session, DRYRUN=False):
    templates = session.template.get(output=["host", "templateid"])
    templates = [{'host': elem['host'], 'templateid': int(elem['templateid'])} for elem in templates]
    return templates


@deflogger
def update_host_name(token, url, host, host_id):
    payload = dict(jsonrpc='2.0',
                   method='host.update',
                   params=dict(hostid=host_id),
                   id=1,
                   auth=token)
    if "host" in host.keys():
        payload["params"]["host"] = host["host"]
    if "name" in host.keys():
        if host["name"]: payload["params"]["name"] = host["name"]
    

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if "error" in response.json():
            print("Error while updating host or name; host ID:", host_id)
        else:
            if "host" in host.keys():
                print("Host ID:", host_id, "new host value:", host["host"])
            if "name" in host.keys():
                print("Host ID:", host_id, "new name value:", host["name"])

@deflogger
def update_host_templates(token, url, host, host_id):
    payload = dict(jsonrpc='2.0',
                   method='host.update',
                   params=dict(hostid=host_id,
                               templates=host["templates"]),
                   id=1,
                   auth=token)
    

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if "error" in response.json():
            print("Error while updating templates; host_ID:", host_id)
            print(str(response.json()))
            print(host["templates"])
        else:
            print("Host ID:", host_id, "new templates:", host["templates"])

@deflogger
def update_hostinterface_ip_dns(token, url, host, host_id):
    payload = dict(jsonrpc='2.0',
                   method='hostinterface.update',
                   params=dict(interfaceid=host["interface_id"]),
                   id=1,
                   auth=token)

    if "ip_address" in host.keys():
        payload["params"]["ip"] = host["ip_address"]
    if "dns" in host.keys():
        payload["params"]["dns"] = host["dns"]
    

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if "error" in response.json():
            print("Error while updating ip or dns; host ID:", host_id)
        else:
            if "ip_address" in host.keys():
                print("Host ID:", host_id, "new IP-address:", host["ip_address"])
            if "dns" in host.keys():
                print("Host ID:", host_id, "new dns:", host["dns"])

@deflogger
def update_hostinterface_type(token, url, host, host_id):
    payload = dict(jsonrpc='2.0',
                   method='hostinterface.update',
                   params=dict(interfaceid=host["interface_id"],
                               type=host["interface_type"]),
                   id=1,
                   auth=token)
    

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)
        if "error" in response.json():
            print("Error while updating interface_type; host ID:", host_id)
        else:
            print("Host ID:", host_id, "new interface_type:", host["interface_type"])

@deflogger
def update_host_groups(token, url, host, host_id):
    payload = dict(jsonrpc='2.0',
                   method='host.update',
                   params=dict(hostid=host_id,
                               groups=host["groups"]),
                   id=1,
                   auth=token)
    

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)
        if "error" in response.json():
            print("Error while updating groups; host ID:", host_id)
        else:
            print("Host ID:", host_id, "new groups:", host["groups"])


@deflogger
def update_host_inventory(token, url, host, host_id):
    payload = dict(jsonrpc='2.0',
                   method='host.update',
                   params=dict(hostid=host_id,inventory={}),
                   id=1,
                   auth=token)
    if "location" in host.keys():
        payload["params"]['inventory']['location'] = host["location"]
        payload["params"]['inventory']['location_lon'] = host["longitude"]
        payload["params"]['inventory']['location_lat'] = host["latitude"]
    

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, payload=payload)
    else:
        response = requests.post (url=url, headers=HEADERS, data=json.dumps(payload), verify=False)

        if "error" in response.json():
            print("Error while updating host or name; host ID:", host_id)
        else:
            if "location" in host.keys():
                print("Host ID:", host_id, "new host location:", host["location"])


def send_trapper_data(sender_param, sender_items):
    # sender_items = "\n".join( ["- {} {}".format(key, str(sender_dict[key])) for key in sender_dict]) + '\n'
    # sender_param = 'zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -i -'.split(" ")

    if not debug_toolkit.DRYRUN:
        try:
            proc  = Popen(args=sender_param, stdin=PIPE, stdout=PIPE, stderr=PIPE)  
            sender_stdout = proc.communicate(input=bytearray(sender_items,'utf-8'))[0]
            return True
        except:
            #logger.warn ("[send_trapper_data] Error calling zabbix_sender.")
            return False
    else:
        if debug_toolkit.DEBUG: 
            print ("{} [send_trapper_data] Would send data to zbx:\n{}".format(datetime.now(), sender_items))
