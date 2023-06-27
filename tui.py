#!/usr/bin/env python3

import sys
import time
import const
import helper
from color import ColorMsg
from configure import Config
from daemon import DaemonRPC
from notary import Notary
from stats import Stats
from logger import logger
import based_58


class TUI():
    def __init__(self):
        self.config = Config()
        self.msg = ColorMsg()
        self.servers = const.DPOW_SERVERS
    
    def configure(self):
        self.config.create()

    def consolidate(self):
        self.notary = Notary()
        if self.notary.configured:
            coin = self.msg.input("Enter coin to consolidate (or ALL): ")
            q = self.msg.input("Force consolidation? (y/n): ")
            if q.lower() == "y":
                force = True
            else:
                force = False                    
            if coin.lower() == "all":
                for coin in const.DPOW_COINS:
                    self.notary.consolidate(coin, force, force)
            elif coin.upper() in const.DPOW_COINS:
                self.notary.consolidate(coin, force, force)
            else:
                self.msg.error(f"Invalid coin '{coin}', try again.")
        else:
            self.msg.error(f"Node configuration missing. Select 'Configure' from the main menu to set your node config.")

    def convert_privkey(self):
        wif = self.msg.input("Enter private key: ")
        for coin in const.DPOW_COINS:
            if coin != "KMD_3P":
                print(f"{coin}: {helper.wif_convert(coin, wif)}")       

    def reset_wallet(self):
        notary = Notary()
        if notary.configured:
            coin = self.msg.input("Enter coin to reset wallet (or ALL): ")
            if coin.lower() == "all":
                for coin in const.DPOW_COINS:
                    notary.reset_wallet(coin)                        
            elif coin.upper() in const.DPOW_COINS:
                notary.reset_wallet(coin)                    
            else:
                self.msg.error(f"Invalid coin '{coin}', try again.")

    def stats(self):
        nnstats = Stats(const.DPOW_COINS)
        while True:
            try:
                nnstats.show()
                print("Ctrl+C to exit to main menu.")
                time.sleep(600)
            except KeyboardInterrupt:
                break

    def list_addresses(self):
        nn = Notary()
        coins_ntx_data = nn.get_coins_ntx_data()
        coins = list(coins_ntx_data.keys())
        coins.sort()
        print()
        for coin in coins:
            self.msg.status(f"{coin:>12}: {coins_ntx_data[coin]['address']:<40}")

    def import_privkey(self):
        nn = Notary()
        config = self.config.load()
        server = self.msg.input(f"Select server {self.servers}: ")
        notary_name = nn.get_notary_from_pubkey(config[f"pubkey_{server}"])
        wif = self.msg.input(f"Enter {notary_name} {server} private key: ")
        # Does it match the pubkey for this server?
        pubkey = config[f"pubkey_{server}"]
        if not helper.validate_wif(pubkey, wif):
            logger.error("Private key does not match public key for this server!")
        else:
            for coin in const.CONF_PATHS[server]:
                # Check to see if already imported
                address = based_58.get_addr_from_pubkey(pubkey, coin)
                daemon = DaemonRPC(coin)
                self.msg.info(f"{coin} Validating {address}...")
                addr_validation = daemon.validateaddress(address)
                if "ismine" not in addr_validation:
                    addr_validation = daemon.getaddressinfo(address)
                self.msg.info(f"{coin} Address: {addr_validation}")
                if "ismine" not in addr_validation:
                    self.msg.info(f"{coin} Importing private key...")
                    wif = helper.wif_convert(coin, wif)
                    r = daemon.importprivkey(wif)
                    self.msg.info(f"{coin} Address: {r}")
                elif not addr_validation["ismine"]:
                    self.msg.info(f"{coin} Importing private key...")
                    wif = helper.wif_convert(coin, wif)
                    r = daemon.importprivkey(wif)
                    self.msg.info(f"Address: {r}")
                else:
                    self.msg.info(f"Address {address} already imported.")

    def start_coin(self):
        notary = Notary()
        coin = self.msg.input("Enter coin to start (or ALL): ")
        if coin.lower() == "all":
            for coin in const.DPOW_COINS:
                notary.start(coin)
        elif coin.upper() in const.DPOW_COINS:
            notary.start(coin)
        else:
            self.msg.error(f"Invalid coin '{coin}', try again.")

    def restart_coin(self):
        notary = Notary()
        coin = self.msg.input("Enter coin to restart (or ALL): ")
        if coin.lower() == "all":
            for coin in const.DPOW_COINS:
                notary.restart(coin)
        elif coin.upper() in const.DPOW_COINS:
            notary.restart(coin)
        else:
            self.msg.error(f"Invalid coin '{coin}', try again.")

    def stop_coin(self):
        notary = Notary()
        coin = self.msg.input("Enter coin to stop (or ALL): ")
        if coin.lower() == "all":
            for coin in const.DPOW_COINS:
                notary.stop(coin)
        elif coin.upper() in const.DPOW_COINS:
            notary.stop(coin)
        else:
            self.msg.error(f"Invalid coin '{coin}', try again.")

    def exit(self):
        sys.exit()