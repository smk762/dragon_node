#!/usr/bin/env python3
import os
import io
import sys
import json
import stat
import time
import string
import random
import os.path
from zipfile import ZipFile
import platform
import mnemonic
import requests
from os.path import expanduser


def colorize(string, color):
    colors = {
        'black':'\033[30m',
        'error':'\033[31m',
        'red':'\033[31m',
        'green':'\033[32m',
        'orange':'\033[33m',
        'blue':'\033[34m',
        'purple':'\033[35m',
        'cyan':'\033[36m',
        'lightgrey':'\033[37m',
        'table':'\033[37m',
        'darkgrey':'\033[90m',
        'lightred':'\033[91m',
        'lightgreen':'\033[92m',
        'yellow':'\033[93m',
        'lightblue':'\033[94m',
        'status':'\033[94m',
        'pink':'\033[95m',
        'lightcyan':'\033[96m',
    }

    if color not in colors:
        return str(string)
    else:
        return colors[color] + str(string) + '\033[0m'


def color_input(msg):
  return input(colorize(msg, "orange"))


def table_print(msg):
  print(colorize(msg, "cyan"))


def info_print(msg):
  print(colorize(msg, "orange"))


def status_print(msg):
  print(colorize(msg, "status"))


def success_print(msg):
  print(colorize(msg, "green"))


def option_print(msg):
  print(colorize(msg, "darkgrey"))


def error_print(msg):
  print(colorize(msg, "error"))


def wait_continue():
  color_input("Press [Enter] to continue...")


def generate_rpc_pass(length):
    rpc_pass = ""
    special_chars = ["@", "~", "-", "_", "|", "(", ")", ":", "+"]
    quart = int(length/4)
    while len(rpc_pass) < length:
        rpc_pass += ''.join(random.sample(string.ascii_lowercase, random.randint(1,quart)))
        rpc_pass += ''.join(random.sample(string.ascii_uppercase, random.randint(1,quart)))
        rpc_pass += ''.join(random.sample(string.digits, random.randint(1,quart)))
        rpc_pass += ''.join(random.sample(special_chars, random.randint(1,quart)))
    str_list = list(rpc_pass)
    random.shuffle(str_list)
    return ''.join(str_list)


# Load or Create MM2.json
# Documentation: https://developers.komodoplatform.com/basic-docs/atomicdex/atomicdex-setup/configure-mm2-json.html#mm2-json
def load_MM2_json():
    if os.path.exists("MM2.json"):
        with open("MM2.json", "r") as f:
            MM2_JSON = json.load(f)
    else:
        table_print("Looks like you dont have an MM2.json file, lets create one now...")
        rpc_password = generate_rpc_pass(16)
        mm2_conf = {
            "gui": "pyMakerbot",
            "netid": 7777,
            "i_am_seed":False,
            "rpc_password": rpc_password,
            "rpcport": 7762,
            "userhome": "/${HOME#\"/\"}"
        }

        msg = "[E]nter seed manually or [G]enerate one? [E/G]: "
        valid_options = ["G", "g", "E", "e"]
        q = color_input(msg)
        while q.lower() not in valid_options:
            error_print(f"Invalid option, try again. Options: {valid_options}")
            q = color_input(msg)

        if q in ["E", "e"]:
            passphrase = color_input("Enter a seed phrase: ")
        else:        
            m = mnemonic.Mnemonic('english')
            passphrase = m.generate(strength=256)

        mm2_conf.update({"passphrase": passphrase})

        with open("MM2.json", "w+") as f:
            json.dump(mm2_conf, f, indent=4)
            status_print("MM2.json file created.")
            status_print("Be sure to make a secure backup of your seed phrase offline!")

        with open("userpass", "w+") as f:
            f.write(f'userpass="{rpc_password}"')
            status_print("userpass file created.")

    with open("MM2.json", "r") as f:
        MM2_JSON = json.load(f)

    return MM2_JSON


# Load or Create config.json
def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config = json.load(f)
    else:
        table_print("Looks like you dont have an config.json file, lets create one now...")
        config = {
            "whitelist": [
                "RDragoNHdwovvsDLSLMiAEzEArAD3kq6FN"
            ],
            "pubkey": "",
            "server": "",
            "addnode": [
                "seed.komodostats.com",
                "seed.webworker.sh",
                "209.222.101.247",
                "199.127.60.142",
                "104.238.221.61",
                "103.195.100.32"
            ],
            "non_antara_addresses": {
                "AYA":"",
                "CHIPS":"",
                "EMC2":"",
                "GLEEC-OLD":"",
                "MCL":"",
                "SFUSD":"",
                "TOKEL":"",
                "VRSC":""
            }
        }

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


        with open("config.json", "w+") as f:
            json.dump(config, f, indent=4)
            status_print("config.json file created.")


    with open("config.json", "r") as f:
        config = json.load(f)

    return config


# Download coins if not existing
def get_coins_file():
    if not os.path.exists("coins"):
        status_print("coins file not found, downloading...")
        url = "https://raw.githubusercontent.com/KomodoPlatform/coins/master/coins"
        coins = requests.get(url).json()

        with open('coins', 'w', encoding='utf-8') as f:
            json.dump(coins, f, ensure_ascii=False, indent=4)

CONFIG = load_config()

HOME = expanduser("~")
SCRIPT_PATH = sys.path[0]
PRICES_API = "https://prices.cipig.net:1717/api/v2/tickers?expire_at=600"
ACTIVATE_COMMANDS = requests.get("http://116.203.120.91:8762/api/atomicdex/activation_commands/").json()["commands"]
LAUNCH_PARAMS = requests.get("http://116.203.120.91:8762/api/info/launch_params/").json()["results"]
DPOW_COINS = requests.get(f"http://116.203.120.91:8762/api/info/dpow_server_coins/?server={CONFIG['server']}&season=Season_5").json()["results"]
DPOW_COINS.append("KMD")
DPOW_COINS.sort()

IMPORT_PRUNED_COINS = ["EMC2", "CHIPS", "AYA", "GLEEC-OLD", "SFUSD", "LTC"]


ERROR_EVENTS = [
  "StartFailed", "NegotiateFailed", "TakerFeeValidateFailed", "MakerPaymentTransactionFailed",
  "MakerPaymentDataSendFailed", "MakerPaymentWaitConfirmFailed", "TakerPaymentValidateFailed",
  "TakerPaymentWaitConfirmFailed", "TakerPaymentSpendFailed", "TakerPaymentSpendConfirmFailed",
  "MakerPaymentWaitRefundStarted", "MakerPaymentRefunded", "MakerPaymentRefundFailed"
  ]


VALID_OP_SYS = ['Linux', 'Darwin', 'Windows']
OP_SYS = platform.system()
if OP_SYS not in VALID_OP_SYS:
    error_print(f"Invalid OS, must be in {VALID_OP_SYS}")
    sys.exit()
if OP_SYS == "Windows":
    OP_SYS = "Windows_NT"
    error_print(f"Windows is not currently supported, but you can try using WSL.\n See https://docs.microsoft.com/en-us/windows/wsl/install")
    sys.exit()


# Load or create MM2.json
MM2_JSON = load_MM2_json()
MM2_USERPASS = MM2_JSON["rpc_password"]
MM2_IP = "http://127.0.0.1:7762"

# Get coins file if needed
get_coins_file()
