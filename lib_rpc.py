#!/usr/bin/env python3
import os
import re
import json
import platform
import requests
from requests.auth import HTTPBasicAuth


def def_data_dir():
    operating_system = platform.system()
    if operating_system == 'Darwin':
        ac_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        ac_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Windows':
        ac_dir = '%s/komodo/' % os.environ['APPDATA']
    return(ac_dir)


def get_creds_from_file(coin):
    ac_dir = def_data_dir()
    if coin == 'KMD':
        coin_config_file = str(ac_dir + '/komodo.conf')
    else:
        coin_config_file = str(ac_dir + '/' + coin + '/' + coin + '.conf')
    with open(coin_config_file, 'r') as f:
        for line in f:
            l = line.rstrip()
            if re.search('rpcuser', l):
                rpc_user = l.replace('rpcuser=', '')
            elif re.search('rpcpassword', l):
                rpc_pass = l.replace('rpcpassword=', '')
            elif re.search('rpcport', l):
                rpc_port = l.replace('rpcport=', '')
    if len(rpc_port) == 0:
        if coin == 'KMD':
            rpc_port = 7771
        else:
            print("rpcport not in conf file, exiting")
            print("check " + coin_config_file)
            exit(1)
    return rpc_user, rpc_pass, rpc_port


def rpc_proxy(coin, method, method_params=None):
    rpc_user, rpc_pass, rpc_port = get_creds_from_file(coin)
    if not method_params:
        method_params = []
    params = {
        "jsonrpc": "1.0",
        "id":"curltest",
        "method": method,
        "params": method_params,
    }
    #print(json.dumps(params))
    try:
        r = requests.post(f"http://127.0.0.1:{rpc_port}", json.dumps(params), auth=HTTPBasicAuth(rpc_user, rpc_pass))
        resp = r.json()
    except requests.exceptions.RequestException as e:
        r = requests.post(f"http://127.0.0.1:{rpc_port}", json.dumps(params))
        resp = r.json()
        if "error" in resp:
            if resp["error"].find("Userpass is invalid"):
                error_print(f"The {coin} daemon is rejecting your rpc_password. Please check it is running.")
                sys.exit()
    return resp


def getinfo():
    print(rpc_proxy("KMD", "getinfo"))


def getblockcount():
    print(rpc_proxy("KMD", "getblockcount"))


def stop():
    print(rpc_proxy("KMD", "getinfo"))
