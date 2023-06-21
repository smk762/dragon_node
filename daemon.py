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
from color import ColorMsg

class DaemonRPC():
    def __init__(self, coin):
        self.msg = ColorMsg()
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
            pass
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
                self.msg.error(f"rpcport not in {self.conf_path}")
        return [rpcuser, rpcpassword, rpcport]

        
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
            # logger.debug(f"RPC: {method} {method_params}")
            resp = r.json()
            return resp
        except requests.exceptions.InvalidURL as e:
            resp = {"error": "Invalid URL"}
        except requests.exceptions.RequestException as e:
            resp = {"result": r.text}
        return resp

    def getinfo(self):
        return self.rpc("getinfo")["result"]
    
    def getnetworkinfo(self):
        return self.rpc("getnetworkinfo")["result"]

    def getbalance(self):
        return self.rpc("getbalance")["result"]

    def dumpprivkey(self, address):
        return self.rpc("dumpprivkey", [address])["result"]

    def sendtoaddress(self, address, amount):
        return self.rpc("sendtoaddress", [address, amount, "", "", True])["result"]

    def gettxoutproof(self, txid):
        return self.rpc("gettxoutproof", [[txid]])["result"]

    def importprunedfunds(self, raw_tx, txoutproof):
        return self.rpc("importprunedfunds", [raw_tx, txoutproof])["result"]

    def createrawtransaction(self, txid):
        return self.rpc("createrawtransaction", [txid])["result"]

    def signrawtransaction(self, rawhex):
        return self.rpc("signrawtransaction", [rawhex])["result"]

    def signrawtransactionwithwallet(self, rawhex):
        return self.rpc("signrawtransactionwithwallet", [rawhex])["result"]

    def sendrawtransaction(self, signedhex):
        return self.rpc("sendrawtransaction", [signedhex])["result"]

    def getrawtransaction(self, txid):
        return self.rpc("getrawtransaction", [txid])["result"]

    def importprivkey(self, pk, height=None):
        if height: 
            return self.rpc("importprivkey", [pk, "", True, height])["result"]
        return self.rpc("importprivkey", [pk, "", False])["result"]

    def stop(self):
        return self.rpc("stop")["result"]

    def get_wallet_addr(self):
        resp = self.rpc("listaddressgroupings")["result"]
        addr = None
        if len(resp) > 0:
            addr = resp[0][0][0]
        return addr

    def validateaddress(self, address: str) -> dict:
        return self.rpc("validateaddress", [address])["result"]

    ## Blocks
    def getblock(self, block) -> dict:
        return self.rpc("getblock", [f"{block}"])["result"]
    
    def getblockcount(self) -> int:
        return self.rpc("getblockcount")["result"]

    def getblockhash(self, height: int) -> dict:
        return self.getblock(height)["hash"]

    def block_tx(self, height: int) -> dict:
        return self.getblock(height)["tx"]
    
    def last_block_time(self, height) -> int:
        if self.coin in ["LTC", "AYA", "EMC2", "MIL", "CHIPS"]:
            hash = self.getbestblockhash()
            blockinfo = self.getblock(hash)
            blocktime = blockinfo["time"]
        else:
            blocktime = self.block_time(height)
        return blocktime
        
    def block_time(self, height: int) -> int:
        blockinfo = self.getblock(height)
        try:
            return blockinfo["time"]
        except:
            return 0

    def getbestblockhash(self) -> str:
        return self.rpc("getbestblockhash")["result"]

    # Wallet
    def listunspent(self) -> dict:
        return self.rpc("listunspent")["result"]

    def unlock_unspent(self):
        locked_unspent = self.get_locked_unspent()
        return self.rpc("lockunspent", [True, locked_unspent])["result"]

    def get_locked_unspent(self):
        return self.rpc("listlockunspent")["result"]

    # Transactions
    def listtransactions(self, count: int=99999999) -> dict:
        return self.rpc("listtransactions", ["*", count])["result"]

    # Mining
    def setgenerate(self, mining=True, cores=1):
        return self.rpc("setgenerate", [mining, cores])["result"]

    # komodo-cli lockunspent true "[{\"txid\":\"a08e6907dbbd3d809776dbfc5d82e371b764ed838b5655e72f463568df1aadf0\",\"vout\":1}]"
    def get_unspendable(self, unspent):
        for utxo in unspent:
            if not utxo["spendable"]:
                logger.info(utxo)
