#!/usr/bin/env python3
import os
import re
import json
import math
import platform
import requests
import subprocess
from requests.auth import HTTPBasicAuth
from lib_helper import *


def get_data_dir(coin):
    if coin == 'KMD':
        data_dir = f"{os.environ['HOME']}/.komodo"
    elif coin == 'LTC':
        data_dir = f"{os.environ['HOME']}/.litecoin"
    elif coin == 'AYA':
        data_dir = f"{os.environ['HOME']}/.aryacoin"
    elif coin == 'CHIPS':
        data_dir = f"{os.environ['HOME']}/.chips"
    elif coin == 'EMC2':
        data_dir = f"{os.environ['HOME']}/.einsteinium"
    elif coin == 'SFUSD':
        data_dir = f"{os.environ['HOME']}/.smartusd"
    elif coin == 'GLEEC-OLD':
        data_dir = f"{os.environ['HOME']}/.gleecbtc"
    elif coin == 'ARRR':
        data_dir = f"{os.environ['HOME']}/.komodo/PIRATE"
    else:
        data_dir = f"{os.environ['HOME']}/.komodo/{coin}"

    return data_dir


def get_creds_from_file(coin):
    data_dir = get_data_dir(coin)
    if coin == 'KMD':
        coin_config_file = f"{data_dir}/komodo.conf"
    elif coin == 'LTC':
        coin_config_file = f"{data_dir}/litecoin.conf"
    elif coin == 'AYA':
        coin_config_file = f"{data_dir}/aryacoin.conf"
    elif coin == 'CHIPS':
        coin_config_file = f"{data_dir}/chips.conf"
    elif coin == 'EMC2':
        coin_config_file = f"{data_dir}/einsteinium.conf"
    elif coin == 'SFUSD':
        coin_config_file = f"{data_dir}/smartusd.conf"
    elif coin == 'GLEEC-OLD':
        coin_config_file = f"{data_dir}/gleecbtc.conf"
    elif coin == 'ARRR':
        coin_config_file = f"{data_dir}/PIRATE.conf"
    else:
        coin_config_file = f"{data_dir}/{coin}.conf"
    rpc_port = -1
    with open(coin_config_file, 'r') as f:
        for line in f:
            l = line.rstrip()
            if re.search('rpcuser', l):
                rpc_user = l.replace('rpcuser=', '')
            elif re.search('rpcpassword', l):
                rpc_pass = l.replace('rpcpassword=', '')
            elif re.search('rpcport', l):
                rpc_port = l.replace('rpcport=', '')
    if rpc_port == -1:
        if coin == 'KMD':
            rpc_port = 7771
        else:
            print("rpcport not in conf file, exiting")
            print("check " + coin_config_file)
            exit(1)
    return rpc_user, rpc_pass, rpc_port


def rpc_proxy(coin, method, method_params=None, get_response_time=False):
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
        r = requests.post(f"http://127.0.0.1:{rpc_port}", json.dumps(params), auth=HTTPBasicAuth(rpc_user, rpc_pass))
        resp = r.json()
        if "error" in resp:
            if resp["error"].find("Userpass is invalid"):
                error_print(f"The {coin} daemon is rejecting your rpc_password. Please check it is running.")
                sys.exit()
    if get_response_time:
        return r.elapsed
    return resp


def get_wallet_response_time(coin):
    return rpc_proxy(coin, "listunspent", None, True)


def getinfo(coin):
    return rpc_proxy(coin, "getinfo")['result']


def getblockcount(coin):
    return rpc_proxy(coin, "getblockcount")['result']


def getbalance(coin):
    return rpc_proxy(coin, "getbalance")['result']


def dumpprivkey(coin, address):
    return rpc_proxy(coin, "dumpprivkey", [address])['result']


def sendtoaddress(coin, address, amount):
    return rpc_proxy(coin, "sendtoaddress", [address, amount, "", "", True])['result']


def gettxoutproof(coin, txid):
    return rpc_proxy(coin, "gettxoutproof", [[txid]])['result']


def importprunedfunds(coin, raw_tx, txoutproof):
    return rpc_proxy(coin, "importprunedfunds", [raw_tx, txoutproof])['result']


def getrawtransaction(coin, txid):
    return rpc_proxy(coin, "getrawtransaction", [txid])['result']


def importprivkey(coin, pk, height=None):
    if height: 
        return rpc_proxy(coin, "importprivkey", [pk, "", True, height])['result']
    return rpc_proxy(coin, "importprivkey", [pk, "", False])['result']


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


def getblock(coin, block):
    return rpc_proxy(coin, "getblock", [f"{block}"])['result']


def getbestblockhash(coin):
    return rpc_proxy(coin, "getbestblockhash")['result']


def get_unspent(coin):
    return rpc_proxy(coin, "listunspent")["result"]

def unlock_unspent(coin):
    locked_unspent = get_locked_unspent(coin)
    return rpc_proxy(coin, "lockunspent", [True, locked_unspent])["result"]

def get_locked_unspent(coin):
    return rpc_proxy(coin, "listlockunspent")["result"]


# komodo-cli lockunspent true "[{\"txid\":\"a08e6907dbbd3d809776dbfc5d82e371b764ed838b5655e72f463568df1aadf0\",\"vout\":1}]"
def get_unspendable(unspent):
    for utxo in unspent:
        if not utxo["spendable"]:
            print(utxo)


def get_launch_params(coin):
    if coin not in LAUNCH_PARAMS:
        return False

    launch_params = LAUNCH_PARAMS[coin].replace("~", os.environ['HOME'])
    launch_params = launch_params.split(" ")
    if CONFIG['pubkey'] != "":
        launch_params.append(f"-pubkey={CONFIG['pubkey']}")    

    if coin == "KMD":
        launch_params.append(f"-minrelaytxfee=0.000035")
        launch_params.append(f"-opretmintxfee=0.004")
        if CONFIG['server'] == "Main":
            launch_params.append(f"-notary=.litecoin/litecoin.conf")

    if coin == "KMD" or CONFIG['server'] == "Main":
        if 'whitelist' in CONFIG:
            for addr in CONFIG["whitelist"]:
                launch_params.append(f"-whitelistaddress={addr}")

        if 'addnode' in CONFIG:
            for ip in CONFIG["addnode"]:
                launch_params.append(f"-addnode={ip}")

    return launch_params


def sweep_kmd():
    unspent = get_unspent("KMD")
    print(f"{len(unspent)} unspent utxos detected")
    balance = 0
    for utxo in unspent:
        if utxo["amount"] != 0.00010000 and utxo["spendable"]:
            balance += utxo["amount"]
    print(f"{balance} KMD in non-split UTXOs")
    print(sendtoaddress("KMD", CONFIG["sweep_address"], round(balance-5, 4)))
    

def get_split_utxo_count(coin, utxo_value=0.00010000):
    if coin in ["EMC2", "AYA"]:
        utxo_value = 0.00100000
    unspent = get_unspent(coin)
    count = 0
    for utxo in unspent:
        if utxo["amount"] == utxo_value:
            count += 1
    return count




def consolidate_kmd(address, balance):
    unlock_unspent("KMD")
    time.sleep(1)
    txid = ""
    balance = 0
    unspendable = []
    unspent = get_unspent("KMD")
    for utxo in unspent:
        if utxo["spendable"]:
            balance += utxo["amount"]
        else:
            print(f"Unspendable: {uxto}")
            unspendable.append(utxo)
    txid = sendtoaddress("KMD", address, math.floor(balance*1000)/1000)
    return unspendable, txid


def get_wallet_tx(coin):
    return rpc_proxy(coin, "listtransactions", ["*", 99999999])['result']


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


def wait_for_start(coin, launch_params):
    i = 0
    while True:
        try:
            i += 1
            if i > 12:
                print(f"Looks like there might be an issue with loading {coin}... Here are the launch params to do it manually:")
                print(launch_params)
            print(f"Waiting for {coin} daemon to restart...")
            time.sleep(30)
            block_height = getblockcount(coin)
            print(block_height)
            if block_height:
                return block_height
        except:
            pass



def get_ntx_stats(coin, wallet_tx):
    last_ntx_time = 0
    last_mined_time = 0
    ntx = []

    for tx in wallet_tx:
        ntx_addr = get_ntx_addr(coin)
        if "address" in tx:
            if tx["address"] == ntx_addr:

                if tx["time"] > last_ntx_time:
                    last_ntx_time = tx["time"]

                if tx["category"] == "send":
                    ntx.append(tx)

            if "generated" in tx:
                if tx["time"] > last_mined_time:
                    last_mined_time = tx["time"]

    ntx_count = len(ntx)
    return ntx_count, last_ntx_time, last_mined_time