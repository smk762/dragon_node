#!/usr/bin/env python3
import os
import json
import socket
import requests
import const
import helper
from logger import logger
from color import ColorMsg

class Iguana():
    def __init__(self, server):
        self.msg = ColorMsg()
        self.server = server
        if self.server not in ["main", "3p"]:
            raise Exception("Error! Invalid server type")
        self.pubkey = helper.get_server_pubkey(self.server)
        self.add_notaries()
        self.server_coins = helper.get_server_coins(self.server)
        self.add_coins()
    
    def add_coins(self):
        for coin in self.server_coins:
            self.addcoin(coin)
        
    def add_notaries(self):
        config = self.get_config()
        for ip in config["seeds"]:
            self.addnotary(ip)
        
    def get_config(self):
        with open(const.IGUANA_CONFIGS[self.server], "r") as f:
            data = json.load(f)
            data["rpcport"] = 7776
            if self.server == "3p":
                data["rpcport"] = 7779
            return data

    def rpc(self, params):
        try:
            config = self.get_config()
            iguana_url = f"http://127.0.0.1:{config['rpcport']}"
            resp = requests.post(iguana_url, json=params).json()
            return resp
        except Exception as e:
            return {"txid": f"Error! Iguana down? {e}"}

    def splitfunds(self, coin: str, utxos: int=40, sats: int=10000) -> dict:
        coin = coin.split("_")[0]
        params={
            "agent": "iguana",
            "method": "splitfunds",
            "satoshis": f"{sats}",
            "sendflag": 1,
            "duplicates": utxos,
            "coin": coin
        }
        return self.rpc(params)

    def addnotary(self, ip_addr):
        params ={
            "agent": "iguana",
            "method": "addnotary",
            "ipaddr": ip_addr
        }
        return self.rpc(params)

    def dpow(self, coin):
        coin = coin.split("_")[0]
        params ={
            "agent": "iguana",
            "method": "dpow",
            "symbol": coin,
            "pubkey": self.pubkey
        }
        return self.rpc(params)
    
    def get_coin_params(self, coin):
        config = self.get_config()
        coin = coin.split("_")[0]
        filename = f"{coin.lower()}_{config['rpcport']}"
        path = f"iguana_coins/{filename}"
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                data["path"] = f'{os.environ["HOME"]}/{data["path"]}'
            return data
        return False

    def addcoin(self, coin):
        params = self.get_coin_params(coin)
        if not params:
            logger.error(f"Error! Coin {coin} not found in iguana_coins")
        return self.rpc(params)
    
    def myipaddr(self):
        params = {
            "agent": "SuperNET",
            "method": "myipaddr",
            "ipaddr": socket.gethostbyname(socket.gethostname())
        }
        return self.rpc(params)

    def help(self):
        params = {
            "agent": "SuperNET",
            "method": "help"
        }
        return self.rpc(params)

    def notarizations(self, coin, height, numblocks=1000):
        coin = coin.split("_")[0]
        params = {
            "pubkey": self.pubkey,
            "agent": "dpow",
            "method": "notarizations",
            "symbol": coin,
            "height": height,
            "numblocks": numblocks
        }
        return self.rpc(params)

    def walletpassphrase(self, passphrase):
        params = {
            "method": "walletpassphrase",
            "params": [passphrase, 9999999]
        }
        return self.rpc(params)


