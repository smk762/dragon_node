#!/usr/bin/env python3
import os
import re
import json
import platform
import requests
import subprocess
from requests.auth import HTTPBasicAuth
from lib_helper import *


def get_data_dir(coin):
    operating_system = platform.system()
    if operating_system == 'Darwin':
        data_dir = os.environ['HOME'] + '/Library/Application Support/Komodo'
    elif operating_system == 'Linux':
        data_dir = os.environ['HOME'] + '/.komodo'
    elif operating_system == 'Windows':
        data_dir = f"/komodo/{os.environ['APPDATA']}"

    if coin != 'KMD':
        data_dir = f"{data_dir}/{coin}"
    return data_dir


def get_creds_from_file(coin):
    data_dir = get_data_dir(coin)
    if coin == 'KMD':
        coin_config_file = f"{data_dir}/komodo.conf"
    else:
        coin_config_file = f"{data_dir}/{coin}.conf"
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


def getinfo(coin):
    print(rpc_proxy(coin, "getinfo"))['result']


def getblockcount(coin):
    return rpc_proxy(coin, "getblockcount")['result']


def getbalance(coin):
    return rpc_proxy(coin, "getbalance")['result']


def dumpprivkey(coin, address):
    return rpc_proxy(coin, "dumpprivkey", [address])['result']


def sendtoaddress(coin, address, amount):
    return rpc_proxy(coin, "sendtoaddress", [address, amount, "", "", True])['result']


def importprivkey(coin, pk, height):
    return rpc_proxy(coin, "importprivkey", [pk, "", True, height])['result']


def stop(coin):
    return rpc_proxy(coin, "stop")['result']


def get_wallet_addr(coin):
    resp = rpc_proxy(coin, "listaddressgroupings")['result']
    addr = None
    if len(resp) > 0:
        addr = resp[0][0][0]
    return addr


def get_pubkey(coin, address):
    return rpc_proxy(coin, "validateaddress", [address])['result']["pubkey"]


def get_unspent(coin, address):
    return rpc_proxy(coin, "listunspent")["result"]


def get_unspendable(unspent):
    for utxo in unspent:
        if not utxo["spendable"]:
            print(utxo)


def get_launch_params(coin):
    launch_params = LAUNCH_PARAMS[coin].replace("~", os.environ['HOME'])
    launch_params = launch_params.split(" ")
    if CONFIG['pubkey'] != "":
        launch_params.append(f"-pubkey={CONFIG['pubkey']}")    

    if coin == "KMD":
        launch_params.append(f"-notary=.litecoin/litecoin.conf")
        launch_params.append(f"-minrelaytxfee=0.000035")
        launch_params.append(f"-opretmintxfee=0.004")

    if 'whitelist' in CONFIG:
        for addr in CONFIG["whitelist"]:
            launch_params.append(f"-whitelistaddress={addr}")

    if 'addnode' in CONFIG:
        for ip in CONFIG["addnode"]:
            launch_params.append(f"-addnode={ip}")

    return launch_params


def sweep_kmd():
    wallet_address = get_wallet_addr("KMD")
    unspent = get_unspent("KMD", wallet_address)
    print(f"{len(unspent)} unspent utxos detected")
    balance = 0
    for utxo in unspent:
        if utxo["amount"] != 0.00010000 and utxo["spendable"]:
            balance += utxo["amount"]
    print(f"{balance} KMD in non-split UTXOs")
    print(sendtoaddress("KMD", CONFIG["sweep_address"], balance-1))
    


def get_wallet_tx_count(coin):
    return len(rpc_proxy(coin, "listtransactions", ["*", 99999999])['result'])


def start_chain(coin, launch_params):
    log_output = open(f"{coin}_daemon.log",'w+')
    subprocess.Popen(launch_params, stdout=log_output, stderr=log_output, universal_newlines=True, preexec_fn=preexec)
    time.sleep(3)
    success_print('{:^60}'.format( f"{coin} daemon starting."))
    success_print('{:^60}'.format( f"Use 'tail -f {coin}_daemon.log' for mm2 console messages."))


def wait_for_stop(coin):
    while True:
        try:
            print(f"Waiting for {coin} daemon to stop...")
            time.sleep(10)
            block_height = getblockcount(coin)
        except requests.exceptions.RequestException as e:
            break
    time.sleep(10)