#!/usr/bin/env python3
import os
import sys
import time
import const
import helper
from color import ColorMsg
from configure import Config
from daemon import DaemonRPC
from notary import Notary
from stats_table import Stats
from iguana import Iguana
from faucet import Faucet
from logger import logger
import based_58

notary = Notary()
msg = ColorMsg()

def show_logo():
    msg.table('''
      ________                                         _____   __     _________      
      ___  __ `____________ _ _____ _____________      ___/ | / /___________/ /____  
      __  / / /_/ ___// __ `/ / __ ` / __ `_/ __ `     __/  |/ / / __ `/ __  / / _ ` 
      _  /_/ /_/ /   / /_/ / / /_/ // /_/ // / / /     _/ /|  / / /_/ / /_/ / /  __/ 
      /_____/ /_/    `__,_/  `__, / `____//_/ /_/      /_/ |_/  `____/`__,_/  `___/  
                            /____/                                                   
    ''')
    msg.ltcyan('{:^80}'.format('Dragon Node menu v0.2 by Dragonhound'))
    print()
    notary.welcome()

def show_menu(menu, menu_name):
    while True:
        try:
            if menu_name == "Main Menu":
                msg.status(f"\n  ==== {menu_name} ====")
            else:
                msg.ltgreen(f"\n  ==== {menu_name} ====")
            for i in range(len(menu)):
                for k, v in menu[i].items():
                    msg.option(f'  [{i}] {k.title().replace("_", " ")}')
            q = msg.input("Select an option: ")
            try:
                q = int(q)
            except ValueError:
                msg.error("Invalid option, try again.")
                continue
            if q >= len(menu):
                msg.error("Invalid option, try again.")
                continue
            else:
                for k, v in menu[q].items():
                    v()
        except KeyboardInterrupt:
            print()
            break


class MainMenu():
    def __init__(self):
        self.cfg = Config()
        self.msg = ColorMsg()
        self.servers = const.DPOW_SERVERS
            
        self.menu = [
            {"stats": self.stats},
            {"config_menu": ConfigMenu().show},
            {"iguana_menu": IguanaMenu().show},
            {"notary_menu": NotaryMenu().show},
            {"wallet_menu": WalletMenu().show},
            {"exit": self.exit}
        ]

    def show(self):
        show_menu(self.menu, "Main Menu")
        
    def logo(self):
        show_logo()

    def stats(self):
        nnstats = Stats(const.DPOW_COINS)
        while True:
            try:
                nnstats.show()
                print()
                self.msg.status(" Ctrl+C to exit to main menu.")
                time.sleep(600)
            except KeyboardInterrupt:
                break

    def exit(self):
        sys.exit()


class NotaryMenu():
    def __init__(self):
        self.cfg = Config()
        self.msg = ColorMsg()
        self.nn = Notary()
        self.faucet = Faucet()
        self.servers = const.DPOW_SERVERS
        self.menu = [
            {"main_menu": self.exit},
            {"notary_faucet": self.drip},
            {"start_mining": self.start_mining},
            {"stop_mining": self.stop_mining},
            {"start_coin": self.start_coin},
            {"stop_coin": self.stop_coin},
            {"migrate_funds_to_pubkey": self.migrate_funds_to_pubkey}
        ]

    def show(self):
        show_menu(self.menu, "Wallet Menu")

    def drip(self):
        balances = self.faucet.balances()
        coin = self.msg.input("Enter coin to drip: ")
        if coin.upper() in const.DPOW_COINS:
            pubkey = self.cfg.load()[f"pubkey_{helper.get_coin_server(coin)}"]
            self.msg.status(self.faucet.drip(coin, pubkey))
        else:
            self.msg.error(f"Invalid coin '{coin}', try again.")

    def start_coin(self):
        coin = self.msg.input("Enter coin to start (or ALL): ")
        if coin.lower() == "all":
            for coin in const.DPOW_COINS:
                self.nn.start(coin)
        elif coin.upper() in const.DPOW_COINS:
            self.nn.start(coin)
        else:
            self.msg.error(f"Invalid coin '{coin}', try again.")

    def stop_coin(self):
        coin = self.msg.input("Enter coin to stop (or ALL): ")
        if coin.lower() == "all":
            for coin in const.DPOW_COINS:
                self.nn.stop(coin)
        elif coin.upper() in const.DPOW_COINS:
            self.nn.stop(coin)
        else:
            self.msg.error(f"Invalid coin '{coin}', try again.")

    def start_mining(self):
        daemon = DaemonRPC("KMD")
        if daemon.is_mining():
            self.msg.darkgrey("Already mining.")
            return
        print(daemon.start_mining())
       
    def stop_mining(self):
        daemon = DaemonRPC("KMD")
        if daemon.is_mining():
            self.msg.darkgrey("Already mining.")
            return
        print(daemon.start_mining())

    def migrate_funds_to_pubkey(self):
        pubkey_main = self.msg.input("Enter pubkey to migrate Main funds to: ")
        pubkey_3p = self.msg.input("Enter pubkey to migrate 3P funds to: ")
        nn = Notary()
        coins_ntx_data = self.cfg.get_coins_ntx_data()
        coins = list(coins_ntx_data.keys())
        coins.sort()
        print()
        
        # Try consolidate first to get any hidden utxos
        for coin in coins:
            server = helper.get_coin_server(coin)
            pubkey = pubkey_main if server == "main" else pubkey_3p
            address = based_58.get_addr_from_pubkey(pubkey, coin)
            k = self.msg.colorize(f"{coin:>12}", "lightblue")
            v = self.msg.colorize(f"{address:<40}", "lightcyan")
            print(f"{k}: {v}")
            try:
                nn.consolidate(coin, True)
            except Exception as e:
                self.msg.error(f"Error consolidating {coin}: {e}")

        for i in range(60):
            msg.status(f"Waiting {60-i} seconds for consolidations to progress...")
            time.sleep(1)

        # Try daemon next to get any funds is change addresses
        for coin in coins:
            server = helper.get_coin_server(coin)
            pubkey = pubkey_main if server == "main" else pubkey_3p
            address = based_58.get_addr_from_pubkey(pubkey, coin)
            try:
                daemon = DaemonRPC(coin)
                balance = daemon.getbalance()
                daemon.sendtoaddress(address, balance, True)
            except Exception as e:
                self.msg.error(f"Error connecting to {coin}: {e}")      

    def exit(self):
        raise KeyboardInterrupt


class WalletMenu():
    def __init__(self):
        self.cfg = Config()
        self.msg = ColorMsg()
        self.servers = const.DPOW_SERVERS
        self.menu = [
            {"main_menu": self.exit},
            {"sweep_kmd": self.sweep_kmd},
            {"consolidate (from API)": self.consolidate_api},
            {"consolidate (from daemon)": self.consolidate_daemon},
            {"reset_wallet": self.reset_wallet},
            {"list_addresses": self.list_addresses},
            {"list_private_keys": self.list_private_keys},
            {"import_private_key": self.import_privkey},
            {"convert_private_key": self.convert_privkey}
        ]

    def show(self):
        show_menu(self.menu, "Wallet Menu")

    def sweep_kmd(self):
        nn = Notary()
        nn.sweep_kmd()

    def consolidate_api(self):
        self.consolidate(True)

    def consolidate_daemon(self):
        self.consolidate(False)
    
    def consolidate(self, api=True):
        config = Config().load()
        if helper.is_configured(config):
            self.notary = Notary()
            if not const.CRYPTOID_API_KEY and api:
                self.msg.status("AYA not yet supported...")
                self.msg.status("EMC2 & MIL need an API key from https://chainz.cryptoid.info/api.dws in your .env file...")
            
            coin = self.msg.input("Enter coin to consolidate (or ALL): ")
            q = self.msg.input("Force consolidation? (y/n): ")
            if q.lower() == "y":
                force = True
            else:
                force = False                    
            if coin.lower() == "all":
                for coin in const.DPOW_COINS:
                    self.notary.consolidate(coin, force, api)
            elif coin.upper() in const.DPOW_COINS:
                self.notary.consolidate(coin.upper(), force, api)
            else:
                self.msg.error(f"Invalid coin '{coin}', try again.")
        else:
            self.msg.error(f"Node configuration missing. Select 'Configure' from the main menu to set your node config.")

    def convert_privkey(self):
        wif = self.msg.input("Enter private key: ")
        for coin in const.DPOW_COINS:
            if coin != "KMD_3P":
                k = self.msg.colorize(f"{coin:>12}", "lightblue")
                v = self.msg.colorize(f"{helper.wif_convert(coin, wif)}", "lightcyan")
                print(f"{k}: {v}")
        self.msg.input("Press enter to continue...")
        os.system('clear')
        show_logo()

    def list_private_keys(self):
        '''Gets KMD pk for each server, then converts and prints for each coin'''
        config = Config().load()
        daemon_main = DaemonRPC("KMD")
        address_main = config["addresses"]["KMD"]
        wif_main = daemon_main.dumpprivkey(address_main)
        for coin in const.COINS_MAIN:
            k = self.msg.colorize(f"{coin:>12}", "lightblue")
            v = self.msg.colorize(f"{helper.wif_convert(coin, wif_main)}", "lightcyan")
            print(f"{k}: {v}")
        daemon_3p = DaemonRPC("KMD_3P")
        address_3p = config["addresses"]["KMD_3P"]
        wif_3p = daemon_3p.dumpprivkey(address_3p)
        for coin in const.COINS_3P:
            k = self.msg.colorize(f"{coin:>12}", "lightblue")
            v = self.msg.colorize(f"{helper.wif_convert(coin, wif_3p)}", "lightcyan")
            print(f"{k}: {v}")
        self.msg.input("Press enter to continue...")
        os.system('clear')
        show_logo()

    def reset_wallet(self):
        self.msg.warning("WARNING: This will delete your wallet.dat, then restart daemons and import your private keys without a rescan.")
        self.msg.warning("Afterwards, a consolidation will be attempted - but not all coins have a supporting API.")
        self.msg.warning("For some third party coins, alternative methods like `importprunefunds` may be required.")
        config = Config().load()
        if helper.is_configured(config):
            notary = Notary()
            coin = self.msg.input("Enter coin to reset wallet (or ALL): ")
            if coin.lower() == "all":
                q = self.msg.input("Exclude coins that can not auto-consolidate? [y/n]: ")
                if q.lower() == "y":
                    notary.reset_wallet_all(True)
                else:
                    notary.reset_wallet_all(False)
            elif coin.upper() in const.DPOW_COINS:
                notary.reset_wallet(coin)                    
            else:
                self.msg.error(f"Invalid coin '{coin}', try again.")

    def list_addresses(self):
        coins_ntx_data = self.cfg.get_coins_ntx_data()
        coins = list(coins_ntx_data.keys())
        coins.sort()
        print()
        for coin in coins:
            k = self.msg.colorize(f"{coin:>12}", "lightblue")
            v = self.msg.colorize(f"{coins_ntx_data[coin]['address']:<40}", "lightcyan")
            print(f"{k}: {v}")

    def import_privkey(self):
        nn = Notary()
        config = self.cfg.load()
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
                if addr_validation is None:
                    addr_validation = daemon.getaddressinfo(address)

                if addr_validation is not None:
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
                else:
                    self.msg.info(f"Unable to validate {coin} address {address} already imported.")
        self.msg.input("Press enter to continue...")
        os.system('clear')
        show_logo()
        
    def exit(self):
        raise KeyboardInterrupt


class ConfigMenu():
    def __init__(self):
        self.cfg = Config()
        self.msg = ColorMsg()
        self.menu = [
            {"main_menu": self.exit},
            {"show_config": self.show_config},
            {"update_config": self.update_config},
            {"show_split_config": self.show_split_config},
            {"update_split_config": self.update_split_config}
        ]

    def show(self):
        show_menu(self.menu, "Configuration Menu")

    def show_split_config(self):
        self.cfg.show_split_config()

    def show_config(self):
        self.cfg.show()

    def update_config(self):
        self.cfg.menu()
        
    def update_split_config(self):
        self.cfg.update("update_split_config")

    def exit(self):
        raise KeyboardInterrupt


class IguanaMenu():
    def __init__(self):
        self.cfg = Config()
        self.msg = ColorMsg()
        self.nn = Notary()
        self.dpow_main = Iguana("main")
        self.dpow_3p = Iguana("3p")
        self.menu = [
            {"main_menu": self.exit},
            {"stop_iguana": self.stop_iguana},
            {"add_coins": self.add_coins},
            {"add_peers": self.add_peers},
            {"dpow_coins": self.dpow_coins},
            {"split_utxos": self.split_utxos}
        ]

    def show(self):
        show_menu(self.menu, "Iguana Menu")

    def add_coins(self):
        for coin in const.COINS_MAIN:
            self.msg.ltblue(f"adding {coin}")
            self.msg.darkgrey(f"{self.dpow_main.addcoin(coin)}")
        for coin in const.COINS_3P:
            self.msg.ltblue(f"adding {coin}")
            self.msg.darkgrey(f"{self.dpow_3p.addcoin(coin)}")

    def add_peers(self):
        config = self.cfg.load()
        for k, v in config["addnotary"].items():
            self.msg.info(f"Adding {k}")
            self.msg.darkgrey(f"{self.dpow_main.addnotary(v)}")
            self.msg.darkgrey(f"{self.dpow_3p.addnotary(v)}")
            for coin in const.DPOW_COINS:
                self.msg.darkgrey(f"{DaemonRPC(coin).addnode(v)}")

    def start_iguana(self):
        self.dpow_main.start()
        self.dpow_3p.start()

    def stop_iguana(self):
        self.dpow_main.stop()
        self.dpow_3p.stop()

    def dpow_coins(self):
        config = self.cfg.load()
        # KMD needs to go first
        self.msg.darkgrey(f"{self.dpow_main.dpow('KMD')}")
        for coin in const.COINS_MAIN:
            self.msg.ltblue(f"adding {coin}")
            self.msg.darkgrey(f"{self.dpow_main.dpow(coin)}")
        for coin in const.COINS_3P:
            self.msg.ltblue(f"adding {coin}")
            self.msg.darkgrey(f"{self.dpow_3p.dpow(coin)}")

    def split_utxos(self):
        coin = self.msg.input("Enter coin to split (or ALL): ")
        q = self.msg.input("Force split? (y/n): ")
        if q.lower() == "y":
            force = True
        else:
            force = False                    
        if coin.lower() == "all":
            for coin in const.DPOW_COINS:
                self.nn.split_utxos(coin, force)
        elif coin.upper() in const.DPOW_COINS:
            self.nn.split_utxos(coin.upper(), force)
        else:
            self.msg.error(f"Invalid coin '{coin.upper()}', try again.")
    def exit(self):
        raise KeyboardInterrupt
