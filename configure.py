#!/usr/bin/env python3
import os
import sys
import json
import const
import color
import based_58
from logger import logger
from dotenv import load_dotenv

load_dotenv()

# Run this to configure your dragon node
# It will create a config.json file and a .env file,
# to store the node configuration and environment variables


class Config():
    def __init__(self):
        self.color_msg = color.ColorMsg()
        self.userhome = os.environ['HOME']
        self.sweep_address = os.getenv("SWEEP_ADDR")
        self.pubkey_main = ""
        self.address_main = ""
        self.pubkey_3p = ""
        self.addresses_3p = {
            "AYA":"",
            "CHIPS":"",
            "EMC2":"",
            "KMD":"",
            "MCL":"",
            "MIL":"",
            "TOKEL":"",
            "VRSC":""
        }
        # We can add these to the daemon conf files
        self.addnode = {
            "komodostats": "seed.komodostats.com",
            "webworker": "seed.webworker.sh",
        }
        # We can add these to the daemon conf files
        self.whitelist = {
            "s6_dragonhound_DEV_main": "RDragoNHdwovvsDLSLMiAEzEArAD3kq6FN",
            "s6_dragonhound_DEV_3p": "RLdmqsXEor84FC8wqDAZbkmJLpgf2nUSkq",
            "s7_dragonhound_DEV_main": "RHi882Amab35uXjqBZjVxgEgmkkMu454KK",
            "s7_dragonhound_DEV_3p": "RHound8PpyhVLfi56dC7MK3ZvvkAmB3bvQ"
        }
        # We can add these to the daemon conf files as addnodes,
        # and with Iguana.addnotary()
        self.addnotary = {
            "dragonhound_AR": "15.235.204.174",
            "dragonhound_NA": "209.222.101.247",
            "dragonhound_DEV": "103.195.100.32"
        }
        self.readonly = ["userhome", "address_main", "addresses_3p", "config", "hidden"]
        self.hidden = ["color_msg", "readonly", "hidden", "display_options", "options", "config"]
        self.config_path = f"{const.SCRIPT_PATH}/config.json"
        self.config = self.load()

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return json.load(f)
        return self.__dict__.copy()
    
    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=4)
    
    def options_legend(self):
        readonly = self.color_msg.colorize("[read only]", "orange")
        missing = self.color_msg.colorize("[missing]", "warning")
        print(f"Legend: {readonly} {missing}")

    def display(self):
        for i in self.config:
            if i not in self.hidden:
                if isinstance(self.config[i], dict):
                    if i in self.readonly:
                        self.color_msg.info(f"{i}:")
                    else:
                        self.color_msg.table(f"{i}:")
                    for j in self.config[i]:
                        if len(self.config[i][j]) == 0:
                            self.color_msg.warning(f"    {j}: {self.config[i][j]}")
                        elif i in self.readonly:
                            self.color_msg.info(f"    {j}: {self.config[i][j]}")
                        else:
                            self.color_msg.table(f"    {j}: {self.config[i][j]}")
                elif i in self.readonly:
                    self.color_msg.info(f"{i}: {self.config[i]}")
                elif len(self.config[i]) is None:
                    self.color_msg.warning(f"{i}: {self.config[i]}")
                elif len(self.config[i]) == 0:
                    self.color_msg.warning(f"{i}: {self.config[i]}")
                else:
                    self.color_msg.table(f"{i}: {self.config[i]}")
        self.options_legend()        

    def show_config(self):
        self.color_msg.status("==== Existing Config ====")
        self.display()

    def get_options(self):
        options = list(set(self.__dict__.keys()) - set(self.readonly) - set(self.hidden))
        options.sort()
        return options
        
    def create(self):
        while True:
            self.show_config()
            self.color_msg.status(f"\n==== Options ====")
            options = self.get_options()
            for i in range(len(options)):
                self.color_msg.option(f"[{i}] Update {options[i]}")
            self.color_msg.option(f"[{len(options)}] Exit")
            q = self.color_msg.input("Select an option:")
            try:
                q = int(q)
            except ValueError:
                self.color_msg.error("Invalid option, try again.")
                continue
            if q == len(options):
                break
            elif q > len(options):
                self.color_msg.error("Invalid option, try again.")
            else:
                self.update(options[q])
    
    def update(self, option):
        options = self.get_options()
        if option not in options:
            self.color_msg.error("Invalid option, will not update.")
            return

        if isinstance(self.config[option], dict):
            if option in ["addnode", "addnotary"]:
                k = self.color_msg.input(f"Enter notary: ")
                v = self.color_msg.input(f"Enter IP address: ")
            elif option in ["whitelist"]:
                k = self.color_msg.input(f"Enter notary: ")
                v = self.color_msg.input(f"Enter address: ")
            else:
                k = self.color_msg.input(f"Enter {option} key: ")
                v = self.color_msg.input(f"Enter {option} value: ")
            self.config[option].update({k: v})
        else:
            v = self.color_msg.input(f"Enter {option} value: ")
            if isinstance(self.config[option], list):
                self.config[option].append(v)
            else:
                self.config[option] = v

        if option in ["pubkey_main", "pubkey_3p"]:
            self.calculate_addresses()
        elif option == "addnotary":
            self.add_notaries_to_addnodes()
        self.save()

    def calculate_addresses(self):
        if self.pubkey_main != "":
            updated = self.address_main = based_58.get_addr_from_pubkey(self.pubkey_main)
            if not updated:
                self.color_msg.warning("Unable to calculate address from pubkey.")
                self.pubkey_main = ""
             
        if self.pubkey_3p != "":
            for coin in self.addresses_3p:
                address = based_58.get_addr_from_pubkey(self.pubkey_3p, coin)
                if not address:
                    self.color_msg.warning(f"Unable to calculate {coin} address from pubkey.")
                    self.pubkey_3p = ""
                    return
                else:
                    self.addresses_3p.update({
                        coin: address
                    })

    def add_notaries_to_addnodes(self):
        for k, v in self.addnotary.items():
            if v not in self.addnode.values():
                self.addnode.update({k: v})


        '''
        whitelist_addresses = color_input("Enter addresses to whitelist, separated by space: \n")
        for addr in whitelist_addresses.split(" "):
            if addr not in config["whitelist"]:
                config["whitelist"].append(addr)


        pubkey = color_input("Enter your pubkey: ")
        config["pubkey"] = pubkey


        sweep_address = color_input("Enter your sweep address: ")
        config["sweep_address"] = sweep_address


        msg = "[M]ain server or [3]rd Party?: "
        server = color_input(msg)
        while server.lower() not in ["m", "3"]:
            error_print(f"Invalid option, try again. Options: {valid_options}")
            server = color_input(msg)

        if server.lower() == "m":
            config["server"] = "Main"
        elif server == "3":
            config["server"] = "Third_Party"

            for coin in config["non_antara_addresses"]:
                non_antara_address = color_input(f"Enter your {coin} address: ")
                config["non_antara_addresses"][coin] = non_antara_address


        with open(f"{SCRIPT_PATH}/config.json", "w+") as f:
            json.dump(config, f, indent=4)
            status_print(f"{SCRIPT_PATH}/config.json file created.")


    with open(f"{SCRIPT_PATH}/config.json", "r") as f:
        config = json.load(f)

    return config
    '''

