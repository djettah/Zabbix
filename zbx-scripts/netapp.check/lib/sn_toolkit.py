#!/usr/bin/env python3

import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
import json

import debug_toolkit
from debug_toolkit import deflogger, dry_request

HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}
TIMEOUT=10
LOGGER=False

@deflogger
def get_table_records(server, user, password, table, query="", DRYRUN=False):
    url = 'http://{}/api/now/table/{}?{}'.format(server,table,query)
    
    if debug_toolkit.DRYRUN and DRYRUN: 
        dry_request(url=url, headers=HEADERS)
    else:
        response = requests.get (url=url, headers=HEADERS, timeout=TIMEOUT, auth=(user, password), verify=False)
        if 'result' in response.json().keys():
            return response.json()['result']
        else:
            print('Error! Incorrect response from get_table_records.\n', response.json())
            exit()

@deflogger
def find_sys_id(field, value, data):
    for record in data:
        if int(record[field]) == value:
            return record['sys_id']

@deflogger
def delete_table_record(table, uid, server, user, password):
    url = 'http://{}/api/now/table/{}/{}'.format(server,table,uid)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, method='delete')
    else:
        response = requests.delete(url, auth=(user, password), headers=headers)
        if response.status_code == 204:
            print('Запись успешно удалена.')
        else:
            print('Статус: {}, Ответ: {}'.format(response.status_code, response.json()))

@deflogger
def modify_table_records(table, uid, new_value, server, user, password):
    url = 'http://{}/api/now/table/{}/{}'.format(server, table, uid)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    #payload = dict(name=new_value)
    payload = dict(host=new_value)

    if debug_toolkit.DRYRUN: 
        dry_request(url=url, headers=HEADERS, method='put', payload=payload)
    else:
        response = requests.put(url, auth=(user, password), headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(' Выполнено.')
        else:
            print('При синхронизации значения возникли проблемы...')
            print(response.json())

@deflogger
def create_table_record(table, new_keys, id_field, server, user, password):
    url = 'http://{}/api/now/table/{}'.format(server,table)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    #for key, value in new_keys.items():
        #payload = dict(id=key, name=value)
    #for new_record in new_keys:
    #    payload = new_record
    for key, value in new_keys.items():
        payload = {id_field:key, 'host':value}

       	if debug_toolkit.DRYRUN: 
            dry_request(url=url, headers=HEADERS, method='post', payload=json.dumps(payload))
        else:
            response = requests.post(url, auth=(user, password), headers=headers, data=json.dumps(payload))
            if response.status_code == 201:
                print('Создана следующая запись "{} - {}"'.format(key, value))
                if debug_toolkit.DEBUG: print(response.json())
            else:
                print('При создании записи "{} - {}" возникли проблемы:'.format(key, value))
                print(response.json())
