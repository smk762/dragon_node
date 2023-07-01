#!/usr/bin/env python3
import os
import json
import const
import color
import based_58
from logger import logger
import helper
from daemon import DaemonRPC

# Run this to configure your dragon node
# It will create a config.json file and a .env file,
# to store the node configuration and environment variables


class Config():
    def __init__(self):
        self.msg = color.ColorMsg()
        config = self.load()
        self.readonly = [
            "userhome", "addresses", "addresses_3p", "address_main_kmd",
            "address_main_ltc", "whitelist", "addnotary", "addnode",
        ]
        self.required = ["sweep_address", "pubkey_main", "pubkey_3p"]

    def load(self, refresh=False) -> dict:
        if not refresh:
            try:
                if os.path.exists(const.APP_CONFIG_PATH):
                    with open(const.APP_CONFIG_PATH, "r") as f:
                        return json.load(f)
            except json.decoder.JSONDecodeError:
                pass
        return self.get_config_template()

    def save(self, data):
        logger.debug(f"Saving config to {const.APP_CONFIG_PATH}")
        for i in list(data.keys()):
            if i in ["address_main_kmd", "address_main_ltc", "addresses_3p"]:
                del data[i]
        with open(const.APP_CONFIG_PATH, "w") as f:
            json.dump(data, f, indent=4)

    def menu(self):
        while True:
            try:
                config = self.load()
                options = list(set(config.keys()) - set(self.readonly))
                options.sort()
                options.insert(0, "Return to Config Menu")
                self.msg.status(f"\n  ==== Config Options ====")
                for i in options:
                    idx = options.index(i)
                    if i == "Return to Config Menu":
                        self.msg.option(f"  [{idx}] {i}")
                    elif config[i] is None:
                        self.msg.warning(f"  [{idx}] Update {i}")
                    elif len(config[i]) == 0:
                        self.msg.warning(f"  [{idx}] Update {i}")
                    elif len(config[i]) == "":
                        self.msg.warning(f"  [{idx}] Update {i}")
                    else:
                        self.msg.option(f"  [{idx}] Update {i}")
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

    def calculate_addresses(self, config: dict) -> dict:
        for i in ["pubkey_main", "pubkey_3p"]:
            pubkey = config[i]
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
                        if "addresses" not in config:
                            config["addresses"] = {}
                        config["addresses"].update({f"{coin}": address})
        return config

    ### Menu Options ###
    def legend(self) -> None:
        readonly = self.msg.colorize("[read only]", "lightblue")
        required = self.msg.colorize("[required]", "warning")
        print(f"Legend: {readonly} {required}")

    def show(self) -> None:
        self.msg.status(f"\n==== Existing Config ====")
        config = self.load()
        for i in config:
            if isinstance(config[i], dict):
                # All dict options are readonly, and one level deep
                self.msg.ltblue(f"{i}: ")
                for j in config[i]:
                    self.msg.ltcyan(f"    {j}: {config[i][j]}")
            elif isinstance(config[i], list):
                self.msg.ltblue(f"{i}: ")
                for j in config[i]:
                    self.msg.ltcyan(f"    {j}")
            elif i in self.readonly:
                k = self.msg.colorize(i, "lightblue")
                v = self.msg.colorize(config[i], "lightcyan")
                print(f"{k}: {v}")
            elif config[i] in [None, ""]:
                self.msg.warning(f"{i}: {config[i]}")
            else:
                self.msg.ltgreen(f"{i}: {config[i]}")
        self.legend()

    def update(self, option):
        config = self.load()
        options = list(config.keys())
        if option not in options:
            self.msg.error("Invalid option, will not update.")
            return
        self.msg.option(f"Current value for {option}: {config[option]}")
        if option == "pubkey_main":
            pubkey = helper.get_dpow_pubkey("main")
            if pubkey != "":
                fn = f"{const.HOME}/dPoW/iguana/pubkey.txt"
                q = self.msg.input(f"Use {pubkey} from {fn}? [y/n]: ")
                if q.lower() == "y":
                    config[option] = pubkey
                    self.save(config)
                    return
        elif option == "pubkey_3p":
            pubkey = helper.get_dpow_pubkey("3p")
            if pubkey != "":
                fn = f"{const.HOME}/dPoW/iguana/pubkey.txt"
                q = self.msg.input(f"Use {pubkey} from {fn}? [y/n]: ")
                if q.lower() == "y":
                    config[option] = pubkey
                    self.save(config)
                    return
        q = self.msg.input(f"Enter {option} value: ")
        if option in ["pubkey_main", "pubkey_3p"]:
            if helper.validate_pubkey(q):
                config[option] = q
                config = self.calculate_addresses(config)
            else:
                self.msg.error(f"{q} is not a valid pubkey.")
                return
        elif option == "sweep_address":
            daemon = DaemonRPC("KMD")
            if "isvalid" in daemon.validateaddress(q):
                if daemon.validateaddress(q)["isvalid"]:
                    config[option] = q
                else:
                    self.msg.error(f"{q} is not a valid KMD address.")
                    return
            else:
                self.msg.error(f"Unable to validate KMD address. Is daemon running?")
                return
        else:
            config[option] = q
        self.save(config)

    ### Templates ###
    def get_config_template(self):
        config = {
            "userhome": const.HOME,
            "sweep_address": "",
            "pubkey_main": helper.get_dpow_pubkey("main"),
            "pubkey_3p": helper.get_dpow_pubkey("3p"),
            "addnode": const.ADDNODES,
            "whitelist": const.ADDRESS_WHITELIST,
            "addnotary": const.NOTARY_PEERS,
            "addresses": {},
            "split amount": 25,
            "split_threshold": 50
        }
        config = self.calculate_addresses(config)
        return config
    