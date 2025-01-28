#!/usr/bin/env python3
import os
import json
import const
import color
import based_58
from typing import List
from logger import logger
import helper
from daemon import DaemonRPC
# Run this to configure your dragon node
# It will create a config.json file and a .env file,
# to store the node configuration and environment variables


class Config():
    def __init__(self):
        self.msg = color.ColorMsg()
        self.config = self.load()
        self.calculate_addresses()
        self.readonly = [
            "userhome", "addresses", "addresses_3p", "address_main_kmd",
            "address_main_ltc", "whitelist", "addnotary", "addnode",
            "split_threshold"
        ]
        self.required = ["sweep_address", "pubkey_main", "pubkey_3p"]

    def load(self) -> dict:
        template = self.get_config_template()
        try:
            if os.path.exists(const.APP_CONFIG_PATH):
                with open(const.APP_CONFIG_PATH, "r") as f:
                    data = json.load(f)
                for i in template:
                    if i not in data:
                        data.update({i: template[i]})
                return data                       
        except json.decoder.JSONDecodeError:
            pass
        return template

    def save(self, data):
        logger.debug(f"Saving config to {const.APP_CONFIG_PATH}")
        for i in list(data.keys()):
            if i in const.OLD_CONFIG_KEYS:
                del data[i]
        with open(const.APP_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def menu(self):
        while True:
            try:
                options = list(set(list(self.config.keys())) - set(self.readonly) - set(const.OLD_CONFIG_KEYS))
                options.sort()
                options.insert(0, "Return to Config Menu")
                self.msg.status(f"\n  ==== Config Options ====")
                for i in options:
                    idx = options.index(i)
                    opt = i.replace("_", " ").title()
                    if i in ["Return to Config Menu", "Add Whitelist Address"]:
                        self.msg.option(f"  [{idx}] {i}")
                    elif i not in self.config:
                        self.msg.warning(f"  [{idx}] Invalid Option! {opt}")
                    elif self.config[i] is None:
                        self.msg.warning(f"  [{idx}] Update {opt}")
                    elif isinstance(self.config[i], (int, float)):
                        self.msg.option(f"  [{idx}] Update {opt}")
                    elif len(self.config[i]) == 0:
                        self.msg.warning(f"  [{idx}] Update {opt}")
                    elif len(self.config[i]) == "":
                        self.msg.warning(f"  [{idx}] Update {opt}")
                    else:
                        self.msg.option(f"  [{idx}] Update {opt}")
                q = self.msg.input("Select Config option: ")
                try:
                    q = int(q)
                except ValueError:
                    self.msg.error("Invalid option, try again.")
                    continue
                if q > len(options):
                    self.msg.error("Invalid option, try again.")
                elif q == 0:
                    break
                else:
                    self.update(options[q])
            except KeyboardInterrupt:
                break

    def calculate_addresses(self) -> dict:
        for i in ["pubkey_main", "pubkey_3p"]:
            pubkey = self.config[i]
            if i == "pubkey_main":
                coins = const.COINS_MAIN
            else:
                coins = const.COINS_3P

            if pubkey != "":
                for coin in coins:
                    address = based_58.get_addr_from_pubkey(pubkey, coin)
                    if not address:
                        self.msg.warning("Unable to calculate {coin} address from pubkey {pubkey}.")
                        break
                    else:
                        if "addresses" not in self.config:
                            self.config["addresses"] = {}
                        self.config["addresses"].update({f"{coin}": address})

    ### Menu Options ###
    
    def show_split_config(self) -> None:
        data = self.get_coins_ntx_data()
        for coin in data:
            self.msg.ltblue(f"{coin}: ")
            if 'split_amount' in data[coin]:
                self.msg.ltcyan(f"    split_amount: {data[coin]['split_amount']}")
            if 'split_threshold' in data[coin]:
                self.msg.ltcyan(f"    split_threshold: {data[coin]['split_threshold']}")

    def show(self) -> None:
        self.msg.status(f"\n==== Existing Config ====")
        for i in self.config:
            mk = i.title().replace("_", " ")
            if isinstance(self.config[i], dict):
                # All dict options are readonly, and one level deep
                self.msg.ltblue(f"{mk}: ")
                for j in self.config[i]:
                    k = self.msg.colorize(j, "lightblue")
                    v = self.msg.colorize(self.config[i][j], "lightcyan")
                    print(f"    {k}: {v}")
            elif isinstance(self.config[i], list):
                self.msg.ltblue(f"{mk}: ")
                for j in self.config[i]:
                    self.msg.ltcyan(f"    {j}")
            elif i in self.readonly:
                k = self.msg.colorize(mk, "lightblue")
                v = self.msg.colorize(self.config[i], "lightcyan")
                print(f"{k}: {v}")
            elif self.config[i] in [None, ""]:
                k = self.msg.colorize(mk, "lightred")
                v = self.msg.colorize(self.config[i], "lightcyan")
                print(f"{k}: {v}")
            else:
                k = self.msg.colorize(mk, "lightblue")
                v = self.msg.colorize(self.config[i], "lightcyan")
                print(f"{k}: {v}")

    def update_daemon_whitelists(self) -> None:
        for coin in const.WHITELIST_COMPATIBLE:
            conf_file = helper.get_conf_path(coin)
            with open(conf_file, 'r') as conf:
                conf_lines = conf.readlines()
            existing_whitelist = [i.split("=")[1].strip() for i in conf_lines if "whitelistaddress" in i]
            new_whitelist = [i for i in self.config["whitelist"].items() if i[1] not in existing_whitelist]
            with open(conf_file, 'a') as conf:
                for k, v in new_whitelist:
                    conf.write(f'whitelistaddress={v} # {k}\n')

    def update_coin_split_config(self, coins: List[str], split_amount: int, split_threshold: int) -> None:
        data = self.get_coins_ntx_data()
        for coin in coins:
            if coin in data:
                data[coin]["split_amount"] = split_amount
                data[coin]["split_threshold"] = split_threshold
            else:
                data.update({coin: {"split_amount": split_amount, "split_threshold": split_threshold}})
        with open(const.COINS_NTX_DATA_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def update(self, option):
        options = list(self.config.keys())
        if option in options:
            self.msg.option(f"Current value for {option}: {self.config[option]}")
        
        if option == "update_split_config":
            coin = helper.input_coin("Enter coin to update (or ALL): ")
            split_amount = helper.input_int("Enter amount of utxos for split: ", 1, 100)
            split_threshold = helper.input_int("Enter minimum utxo threshold: ", 1, 100)
            if coin.upper() == "ALL":
                self.update_coin_split_config(const.DPOW_COINS, split_amount, split_threshold)
            elif coin.upper() in const.DPOW_COINS:
                self.update_coin_split_config([coin.upper()], split_amount, split_threshold)
            else:
                self.msg.error(f"Invalid coin '{coin}', try again.")
            return
            
        elif option == "Add Whitelist Address":
            while True:
                v = self.msg.input(f"Enter KMD address for whitelist: ")
                daemon = DaemonRPC("KMD")
                r = daemon.validateaddress(v)
                if "isvalid" in r:
                    if r["isvalid"]:
                        if "whitelist" not in self.config:
                            self.config["whitelist"] = const.ADDRESS_WHITELIST
                        k = self.msg.input(f"Enter label for {v}: ")
                        self.config["whitelist"].update({k: v})
                        # Update daemon confs
                        self.update_daemon_whitelists()
                        self.save()
                        self.msg.success(f"Added {v} to whitelist.")
                        break
                    else:
                        self.msg.error(f"{v} is not a valid KMD address.")
                else:
                    self.msg.error(f"Unable to validate address, KMD daemon is not responding. {r}")
                    break
            
        elif option == "pubkey_main":
            pubkey = helper.get_dpow_pubkey("main")
            if pubkey != "":
                fn = f"{const.HOME}/dPoW/iguana/pubkey.txt"
                q = self.msg.input(f"Use {pubkey} from {fn}? [y/n]: ")
                if q.lower() == "y":
                    self.config[option] = pubkey
                    self.save()
                    return
        elif option == "pubkey_3p":
            pubkey = helper.get_dpow_pubkey("3p")
            if pubkey != "":
                fn = f"{const.HOME}/dPoW/iguana/pubkey.txt"
                q = self.msg.input(f"Use {pubkey} from {fn}? [y/n]: ")
                if q.lower() == "y":
                    self.config[option] = pubkey
                    self.save()
                    return

        while True:
            q = self.msg.input(f"Enter {option} value: ")
            if option in ["pubkey_main", "pubkey_3p"]:
                if helper.validate_pubkey(q):
                    self.config[option] = q
                    self.calculate_addresses()
                    break
                else:
                    self.msg.error(f"{q} is not a valid pubkey.")
            elif option == "sweep_address":
                daemon = DaemonRPC("KMD")
                while True:
                    if "isvalid" in daemon.validateaddress(q):
                        if daemon.validateaddress(q)["isvalid"]:
                            self.config[option] = q
                            self.save()
                            return
                        else:
                            self.msg.error(f"{q} is not a valid KMD address.")
                    else:
                        self.msg.error(f"Unable to validate KMD address. Is daemon running?")
                        return
            else:
                self.config[option] = q
        self.save()

    def get_coins_ntx_data(self) -> dict:
        data = {}
        if os.path.exists(const.COINS_NTX_DATA_PATH):
            with open(const.COINS_NTX_DATA_PATH, 'r') as file:
                try:
                    data = json.load(file)
                except Exception as e:
                    pass
        if data == {}:
            data = self.get_coins_data()
        else:
            for coin in const.COINS_MAIN:
                if coin not in data:
                    data.update({
                        coin: self.get_coin_data("main", coin)
                    })

        with open(const.COINS_NTX_DATA_PATH, "w") as file:
            json.dump(data, file, indent=4)
        return data
    
    def get_coins_data(self) -> dict:
        coins_data = {}
        if helper.is_configured(self.config):
            for server in const.CONF_PATHS:
                for coin in const.CONF_PATHS[server]:
                    coins_data.update({
                        coin: self.get_coin_data(server, coin)
                    })
        return coins_data

    def get_coin_data(self, server, coin):
        fee = helper.get_tx_fee(coin)
        return {
            "conf": const.CONF_PATHS[server][coin],
            "wallet": helper.get_wallet_path(coin),
            "utxo_value": helper.get_utxo_value(coin),
            "utxo_value_sats": helper.get_utxo_value(coin, True),
            "split_threshold": 20,
            "split_amount": 20,
            "server": server,
            "address": self.config["addresses"][coin],
            "txfee": f'{fee:.5f}',
            "pubkey": self.config[f"pubkey_{server}"]
        }

    ### Templates ###
    def get_config_template(self):
        return {
            "userhome": const.HOME,
            "sweep_address": "",
            "pubkey_main": helper.get_dpow_pubkey("main"),
            "pubkey_3p": helper.get_dpow_pubkey("3p"),
            "addnode": const.ADDNODES,
            "whitelist": const.ADDRESS_WHITELIST,
            "addnotary": const.NOTARY_PEERS,
            "addresses": {}
        }
    
