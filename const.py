#!/usr/bin/env python3
import os
import sys
import json
from os.path import expanduser, dirname, realpath

# Path constants
HOME = expanduser('~')
DPOW_PATH = f'{HOME}/dPoW'

COMPOSE_PATH_MAIN = f'{HOME}/notary_docker_main/docker-compose.yml'
COMPOSE_PATH_3P = f'{HOME}/notary_docker_3p/docker-compose.yml'

SCRIPT_PATH = dirname(realpath(sys.argv[0]))
COINS_NTX_DATA_PATH = f'{SCRIPT_PATH}/coins_ntx_data.json'
APP_CONFIG_PATH = f"{SCRIPT_PATH}/config.json"

COINS_CONFIG_URL = "https://raw.githubusercontent.com/KomodoPlatform/coins/master/utils/coins_config.json"
COINS_CONFIG_PATH = f"{SCRIPT_PATH}/coins_config.json"

COMMIT_HASHES_URL = "https://raw.githubusercontent.com/KomodoPlatform/dPoW/season-seven/README.md"
COMMIT_HASHES_PATH = f"{SCRIPT_PATH}/commit_hashes.json"

# Coins constants
COINS_MAIN = ["PIRATE", "CCL", "CLC", "ILN", "SUPERNET", "DOC", "MARTY", "LTC", "GLEEC", "KOIN", "THC", "KMD", "NINJA"]
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
DPOW_SERVERS = list(CONF_PATHS.keys())
COINS_3P = list(CONF_PATHS["3p"].keys())
DPOW_COINS = COINS_3P + COINS_MAIN
IMPORT_PRUNED_COINS = ["EMC2", "CHIPS", "AYA", "MIL", "LTC"]
LARGE_UTXO_COINS = ["EMC2", "AYA"]

# Notarisation constants
UTXO_AMT = 0.00010000
NTX_AMT = -0.00083600
MAX_TX_COUNT = 2000
NTX_ADDR = {
    "LTC": "LhGojDga6V1fGzQfNGcYFAfKnDvsWeuAsP",
    "KMD": "RXL3YXG2ceaB6C5hfJcN4fvmLH2C34knhA",
    "EMC": "EfCkxbDFSn4X1VKMzyckyHaXLf4ithTGoM",
    "AYA": "Adpj7WENLyRkq9vVknHa82rf3cVHjYvzCG",
    "MIL": "MVx1hSH9WqwQurgqR7HBDRCu3ESkuhQC8r"
}

PUBKEYS_MAIN = json.load(open("notary_pubkeys.json", "r"))
PUBKEYS_3P = json.load(open("notary_pubkeys_3p.json", "r"))

IGUANA_CONFIGS = {
    "main": f"{DPOW_PATH}/iguana/elected",
    "3p": f"{DPOW_PATH}/iguana/3rd_party"
}

IGUANA_BIN_MAIN = f"{DPOW_PATH}/iguana/m_notary_main"
IGUANA_BIN_3P = f"{DPOW_PATH}/iguana/m_notary_3rdparty_docker"

# These are not used for anything yet, but will be used in the future to update daemon confs
ADDRESS_WHITELIST = {
    "s6_dragonhound_DEV_main": "RDragoNHdwovvsDLSLMiAEzEArAD3kq6FN",
    "s6_dragonhound_DEV_3p": "RLdmqsXEor84FC8wqDAZbkmJLpgf2nUSkq",
    "s7_dragonhound_DEV_main": "RHi882Amab35uXjqBZjVxgEgmkkMu454KK",
    "s7_dragonhound_DEV_3p": "RHound8PpyhVLfi56dC7MK3ZvvkAmB3bvQ"
}
# These are not used for anything yet, but will be used in the future to add peers to daemons and iguana
NOTARY_PEERS = {
    "dragonhound_AR": "15.235.204.174",
    "dragonhound_NA": "209.222.101.247",
    "dragonhound_DEV": "103.195.100.32"
}
# These are not used for anything yet, but will be used in the future to add peers to daemons
ADDNODES = {
    "komodostats": "seed.komodostats.com",
    "webworker": "seed.webworker.sh",
}
