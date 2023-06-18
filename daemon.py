#!/usr/bin/env python3
import os
import re
import sys
import json
import const
import helper
import requests
from slickrpc import Proxy
from requests.auth import HTTPBasicAuth
from logger import logger

class DaemonRPC():
    def __init__(self, coin):
        self.coin = coin
        self.conf_path = helper.get_conf_path(coin)
        self.creds = self.get_creds()
        self.rpcuser = self.creds[0]
        self.rpcpass = self.creds[1]
        self.rpcport = self.creds[2]

    def get_creds(self):
        rpcport = 0
        rpcuser = ''
        rpcpassword = ''
        if not os.path.exists(self.conf_path):
            print(f"{self.conf_path} not found!")
        else:
            with open(self.conf_path, 'r') as f:
                for line in f:
                    l = line.rstrip()
                    if re.search('rpcuser', l):
                        rpcuser = l.replace('rpcuser=', '')
                    elif re.search('rpcpassword', l):
                        rpcpassword = l.replace('rpcpassword=', '')
                    elif re.search('rpcport', l):
                        rpcport = int(l.replace('rpcport=', ''))
            if rpcport == 0:
                logger.error(f"rpcport not in {self.conf_path}")
        return [rpcuser, rpcpassword, rpcport]

    def rpc_response_time(self, method: str, method_params: object=None) -> dict:
        if not method_params:
            method_params = []
        params = {
            "jsonrpc": "1.0",
            "id":"curltest",
            "method": method,
            "params": method_params,
        }
        try:
            r = requests.post(
                f"http://127.0.0.1:{self.rpcport}",
                json.dumps(params),
                auth=HTTPBasicAuth(self.rpcuser, self.rpcpass),
                timeout=90
            )
            return {"result": r.elapsed}
        except requests.exceptions.InvalidURL as e:
            return {"error": "Invalid URL"}
        except requests.exceptions.RequestException as e:
            return {"error": e}
    
        
    def rpc(self, method: str, method_params: object=None) -> dict:
        if not method_params:
            method_params = []
        params = {
            "jsonrpc": "1.0",
            "id":"curltest",
            "method": method,
            "params": method_params,
        }
        r = requests.post(
            f"http://127.0.0.1:{self.rpcport}",
            json.dumps(params),
            auth=HTTPBasicAuth(self.rpcuser, self.rpcpass),
            timeout=90
        )
        try:
            resp = r.json()
            if "error" in resp:
                if resp["error"]:
                    print(resp["error"])
            logger.debug(f"RPC: {method} {method_params}")
            logger.debug(f"{resp}")
        except requests.exceptions.InvalidURL as e:
            resp = {"error": "Invalid URL"}
        except requests.exceptions.RequestException as e:
            resp = {"result": r.text}
        return resp


    def getinfo(self):
        return self.rpc("getinfo")


    def getbalance(self):
        return self.rpc("getbalance")


    def dumpprivkey(self, address):
        return self.rpc("dumpprivkey", [address])


    def sendtoaddress(self, address, amount):
        return self.rpc("sendtoaddress", [address, amount, "", "", True])


    def gettxoutproof(self, txid):
        return self.rpc("gettxoutproof", [[txid]])


    def importprunedfunds(self, raw_tx, txoutproof):
        return self.rpc("importprunedfunds", [raw_tx, txoutproof])


    def getrawtransaction(self, txid):
        return self.rpc("getrawtransaction", [txid])


    def importprivkey(self, pk, height=None):
        if height: 
            return self.rpc("importprivkey", [pk, "", True, height])
        return self.rpc("importprivkey", [pk, "", False])


    def stop(self):
        return self.rpc("stop")


    def get_wallet_addr(self):
        resp = self.rpc("listaddressgroupings")
        addr = None
        if len(resp) > 0:
            addr = resp[0][0][0]
        return addr


    def validateaddress(self, address: str) -> dict:
        return self.rpc("validateaddress", [address])

    ## Blocks
    def getblockcount(self) -> int:
        return self.rpc("getblockcount")["result"]

    def getblock(self, block: int) -> dict:
        return self.rpc("getblock", [f"{block}"])["result"]

    def getblockhash(self, height: int) -> dict:
        return self.getblock(height)["hash"]

    def block_tx(self, height: int) -> dict:
        return self.getblock(height)["tx"]
    
    def block_time(self, height: int) -> dict:
        return self.getblock(height)["time"]

    def getbestblockhash(self) -> dict:
        height = self.getblockcount()
        return self.getblockhash(height)

    # Wallet
    def get_unspent(self) -> dict:
        return self.rpc("listunspent")

    def unlock_unspent(self):
        locked_unspent = self.get_locked_unspent()
        return self.rpc("lockunspent", [True, locked_unspent])

    def get_locked_unspent(self):
        return self.rpc("listlockunspent")

    # Transactions
    def listtransactions(self, count: int=99999999) -> dict:
        return self.rpc("listtransactions", ["*", count])

    # Mining
    def setgenerate(self, mining=True, cores=1):
        return self.rpc("setgenerate", [mining, cores])



    # komodo-cli lockunspent true "[{\"txid\":\"a08e6907dbbd3d809776dbfc5d82e371b764ed838b5655e72f463568df1aadf0\",\"vout\":1}]"
    def get_unspendable(self, unspent):
        for utxo in unspent:
            if not utxo["spendable"]:
                print(utxo)
