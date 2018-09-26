#!/usr/bin/env python3

import re
import json

import debug_toolkit
from debug_toolkit import deflogger, dry_request


@deflogger
def sort_sn_hosts_with_templates(row_hosts):
    sorted_hosts = []
    for host in row_hosts:
        if host["x_itgra_monitoring_zabbix_template"]["value"]:
            sorted_hosts.append(host)
    if sorted_hosts:
        return sorted_hosts
    else:
        print("\nNo CMDB items, containing templates. Script finished.")
        exit()


@deflogger
def compare_and_find_new_hosts(zbx_hosts, sn_cis):
    zabbix_uids = [host['inventory']['alias'] for host in zbx_hosts if host['inventory']]
    new, old = None, None
    new = [item for item in sn_cis if item['sys_id']["value"] not in zabbix_uids]
    old = [item for item in sn_cis if item['sys_id']["value"] in zabbix_uids]
    return new, old


@deflogger
def compare_and_find_new_groups(hosts, old_groups):
    new_classes = list(set([host['sys_class_name']["display_value"] for host in hosts]))
    old_group_names = list(set([item['name'] for item in old_groups]))
    new_groups = ['ServiceNow/CMDB/' + nc for nc in new_classes if 'ServiceNow/CMDB/' + nc not in old_group_names]
    if new_groups:
        return new_groups
    else:
        return None


@deflogger
def order_zbx_templates_data(zbx_sn_hosts):
    for host in zbx_sn_hosts:
        template_ids_list = []
        for template in host["parentTemplates"]:
            template_ids_list.append(template["templateid"])
        host["parentTemplates"] = template_ids_list
    #return zbx_sn_hosts


@deflogger
def correct_names(sn_hosts):
    for host in sn_hosts:
        host["name"]["value"] = re.sub('[^a-zA-Z0-9._ -]','_',host["name"]["value"])
        host['sys_class_name']["display_value"] = re.sub('[^a-zA-Z0-9._ -]','_',host['sys_class_name']["display_value"])
        exceeding = len(host["name"]["value"] + "_" + host["sys_id"]["value"]) - 128
        if exceeding > 0:
            host["name"]["value"] = host["name"]["value"][:-exceeding]
    
    #return sn_hosts


@deflogger
def split_sn_templates_data(sn_hosts):
    for host in sn_hosts:
        template_ids = host["x_itgra_monitoring_zabbix_template"]["value"].replace(" ","").split(",")
        host["x_itgra_monitoring_zabbix_template"]["value"] = template_ids
    #return sn_hosts


@deflogger
def sort_zbx_hosts_for_creating(zbx_hosts, sn_templates_index, sn_proxies_index, sn_locations_index):
    for zbx_host in zbx_hosts:
        templates_sys_ids = zbx_host["x_itgra_monitoring_zabbix_template"]["value"]
        proxy_sys_id = zbx_host["x_itgra_monitoring_zabbix_proxy"]["value"]

        #zbx_host["x_itgra_monitoring_zabbix_template"]["value"] = list(map(lambda sys_id: sn_templates_indexed[sys_id]['id'], templates_sys_ids))
        zbx_host["x_itgra_monitoring_zabbix_template"]["value"] = [sn_templates_index[sys_id]['templateid'] for sys_id in templates_sys_ids]
        if sn_proxies_index.get(proxy_sys_id): zbx_host["x_itgra_monitoring_zabbix_proxy"]["value"] = sn_proxies_index[proxy_sys_id]['proxyid']
        zbx_host["latitude"] = zbx_host["longitude"] = {}
        if zbx_host['location']["value"]:
            zbx_host["latitude"]["value"] = sn_locations_index[zbx_host['location']["value"]]['latitude']
            zbx_host["longitude"]["value"] = sn_locations_index[zbx_host['location']["value"]]['longitude']
        else:
            zbx_host["latitude"]["value"] = zbx_host["longitude"]["value"] = ''


@deflogger
def sort_zbx_hosts_for_updating(sn_old_hosts, zbx_old_hosts, zbx_sn_groups, export_group_id, sn_templates_indexed, sn_locations_index):
    data_for_updating = {}
    for sn_host in sn_old_hosts:
        alias = sn_host["sys_id"]["value"]
        host_id = zbx_old_hosts[alias]["hostid"]
        data_for_updating[host_id] = {}
        
        if sn_host["name"]["value"] != zbx_old_hosts[alias]["name"]:
            data_for_updating[host_id]["name"] = sn_host["name"]["value"]
        
        if sn_host["name"]["value"]+"_"+sn_host["sys_id"]["value"] != zbx_old_hosts[alias]["host"]:
            data_for_updating[host_id]["host"] = sn_host["name"]["value"]+"_"+sn_host["sys_id"]["value"]
            if "name" not in data_for_updating[host_id].keys():
                data_for_updating[host_id]["name"] = sn_host["name"]["value"]

        new_templates = []
        sn_host_templates = sn_host['x_itgra_monitoring_zabbix_template']["value"]
        zbx_host_templates = zbx_old_hosts[alias]["templates"]
        #print(sn_host)

        for tpl in sn_host_templates:
            if not sn_templates_indexed.get(tpl): 
                print ("[warn] can't find template with sys_id " + tpl + 'for host' + sn_host["name"]["value"])
                break
            #print(tpl)
            if sn_templates_indexed[tpl]['templateid'] not in zbx_host_templates:
                new_templates.append(sn_templates_indexed[tpl]['templateid'])
        if new_templates:
            zbx_host_templates.extend(new_templates)
            data_for_updating[host_id]["templates"] = zbx_host_templates

        if len(zbx_old_hosts[alias]["interfaces"]) == 1:
            if sn_host["ip_address"]["value"] != zbx_old_hosts[alias]["interfaces"][0]["ip"]:
                data_for_updating[host_id]["ip_address"] = sn_host["ip_address"]["value"]
                data_for_updating[host_id]["interface_id"] = zbx_old_hosts[alias]["interfaces"][0]["interfaceid"]
                #print("\nHost: ", sn_host["name"]["value"])
                #print("IP-address from ServiceNow: ", sn_host["ip_address"]["value"])
                #print("IP-address from Zabbix: ", zbx_old_hosts[alias]["interfaces"][0]["ip"], "\n")
            if sn_host["fqdn"]["value"]:
                if zbx_old_hosts[alias]["interfaces"][0]["dns"] != sn_host["fqdn"]["value"]:
                    data_for_updating[host_id]["dns"] = sn_host["fqdn"]["value"]
                    if "interface_id" not in data_for_updating[host_id].keys():
                        data_for_updating[host_id]["interface_id"] = zbx_old_hosts[alias]["interfaces"][0]["interfaceid"]
                    #print("\nHost: ", sn_host["name"]["value"])
                    #print("FQDN from ServiceNow: ", sn_host["fqdn"]["value"])
                    #print("DNS from Zabbix: ", zbx_old_hosts[alias]["interfaces"][0]["dns"], "\n")
        
        if sn_host["sys_class_name"]["display_value"] == "Linux Server" or sn_host["sys_class_name"]["display_value"] == "Windows Server":
            if zbx_old_hosts[alias]["interfaces"][0]["type"] == "2":
                data_for_updating[host_id]["interface_type"] = 1
                data_for_updating[host_id]["interface_id"] = zbx_old_hosts[alias]["interfaces"][0]["interfaceid"]
        else:
            if zbx_old_hosts[alias]["interfaces"][0]["type"] == "1":
                data_for_updating[host_id]["interface_type"] = 2
                data_for_updating[host_id]["interface_id"] = zbx_old_hosts[alias]["interfaces"][0]["interfaceid"]
        
        sn_groups = []
        for group in zbx_old_hosts[alias]["groups"]:
            if "ServiceNow/CMDB/" in group["name"]:
                sn_groups.append(group["name"].replace("ServiceNow/CMDB/", ""))
        
        if len(sn_groups) == 1 and sn_groups[0] == sn_host["sys_class_name"]["display_value"]:
            pass
        else:
            data_for_updating[host_id]["groups"] = [{"groupid":export_group_id}]
            for zbx_sn_group in zbx_sn_groups:
                if zbx_sn_group["name"] == "ServiceNow/CMDB/" + sn_host["sys_class_name"]["display_value"]:
                    data_for_updating[host_id]["groups"].append({"groupid":zbx_sn_group["groupid"]})
                    break
        

        # update location
        #print(zbx_old_hosts[alias])
        if sn_host["location"]["display_value"] != zbx_old_hosts[alias]["location"]:
            data_for_updating[host_id]["location"] = sn_host["location"]["display_value"]
            data_for_updating[host_id]["latitude"] = sn_locations_index[sn_host['location']["value"]]['latitude']
            data_for_updating[host_id]["longitude"] = sn_locations_index[sn_host['location']["value"]]['longitude']

        if not data_for_updating[host_id]:
            del(data_for_updating[host_id])
    return data_for_updating