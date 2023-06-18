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
import requests
from os.path import expanduser
from dotenv import load_dotenv

load_dotenv()

# Path constants
HOME = expanduser('~')
SCRIPT_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
SWEEP_ADDR = os.getenv("SWEEP_ADDR")



# Coins constants
COINS_MAIN = ["PIRATE", "CCL", "KMD", "CLC", "ILN", "SUPERNET", "DOC", "MARTY", "LTC", "GLEEC", "KOIN", "THC", "KMD"]
CONF_PATHS = {
    "main": {
        "KMD": f"{HOME}/.komodo/komodo.conf",
        "LTC": f"{HOME}/.litecoin/litecoin.conf",
    },
    "3p": {
        "KMD_3P": f"{HOME}/.komodo_3p/komodo.conf",
        "VRSC": f"{HOME}/.komodo_3p/VRSC/VRSC.conf",
        "TOKEL": f"{HOME}/.komodo_3p/TOKEL/TOKEL.conf",
        "MCL": f"{HOME}/.komodo_3p/MCL/MCL.conf",
        "AYA": f"{HOME}/.aryacoin/aryacoin.conf",
        "EMC2": f"{HOME}/.einsteinium/einsteinium.conf",
        "MIL": f"{HOME}/.mil/mil.conf",
        "CHIPS": f"{HOME}/.chips/chips.conf"
    }    
}
# Autopopulate conf paths for all main coins
[CONF_PATHS["main"].update({coin: f"{HOME}/.komodo/{coin}/{coin}.conf"}) for coin in COINS_MAIN if coin not in ["KMD", "LTC"]]
COINS_3P = list(CONF_PATHS["3p"].keys())
IMPORT_PRUNED_COINS = ["EMC2", "CHIPS", "AYA", "MIL", "LTC"]
DPOW_COINS = COINS_3P + COINS_MAIN
LARGE_UTXO_COINS = ["EMC2", "AYA"]
DPOW_SERVERS = list(CONF_PATHS.keys())

# Notarisation constants
UTXO_AMT = 0.00010000
NTX_AMT = -0.00083600
MAX_TX_COUNT = 2000
NTX_ADDR = {
    "LTC": "LhGojDga6V1fGzQfNGcYFAfKnDvsWeuAsP",
    "KMD": "RXL3YXG2ceaB6C5hfJcN4fvmLH2C34knhA",
    "EMC": "EfCkxbDFSn4X1VKMzyckyHaXLf4ithTGoM",
    "AYA": "Adpj7WENLyRkq9vVknHa82rf3cVHjYvzCG",
    "GLEEC-OLD": "FTsxvoops8zGeMbY3pHPwY86bfacGvMdfU",
    "SFUSD": "SjLrVr9tkBxoYVVxjZcKX3k8Dno2A28YD7"        
}

'''
PRICES_API = "https://prices.cipig.net:1717/api/v2/tickers?expire_at=600"
ACTIVATE_COMMANDS = requests.get("https://stats.kmd.io/api/atomicdex/activation_commands/").json()["commands"]
LAUNCH_PARAMS = requests.get("https://stats.kmd.io/api/info/launch_params/").json()["results"]
BASE58_PARAMS = requests.get("https://stats.kmd.io/api/info/base_58/").json()["results"]
'''

