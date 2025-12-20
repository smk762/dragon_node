#!/usr/bin/env python3
import os
import sys
import json
import requests
from os.path import expanduser, dirname, realpath
from dotenv import load_dotenv
load_dotenv()


def get_cache_data(file):
    if not os.path.exists(file):
        print(f"Failed to get {file} from cache")
        return {}
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        print(f"{file} from cache is broken!")
        return {}

# Path constants
HOME = expanduser('~')
DPOW_PATH = f'{HOME}/dPoW'

COMPOSE_PATH_MAIN = f'{HOME}/notary_docker_main/docker-compose.yml'
COMPOSE_PATH_3P = f'{HOME}/notary_docker_3p/docker-compose.yml'

SCRIPT_PATH = dirname(realpath(sys.argv[0]))



VERSION_PATH = f"{SCRIPT_PATH}/version.json"
VERSION = json.load(open(VERSION_PATH))['version']
CURRENT_VERSION_URL = "https://raw.githubusercontent.com/smk762/dragon_node/refs/heads/season-8-dev/version.json"
try:
    x = requests.get(CURRENT_VERSION_URL).json()
    CURRENT_VERSION = x['version']
except Exception as e:
    CURRENT_VERSION = VERSION
    logger.debug(e)

DPOW_VERSION_URL = "https://raw.githubusercontent.com/KomodoPlatform/dPoW/refs/heads/master/iguana/version"


ASSETCHAINS_PATH = f"{HOME}/dPoW/iguana/assetchains.json"
with open(ASSETCHAINS_PATH, "r") as f:
    ASSETCHAINS = json.load(f)

COINS_CONFIG_URL = "https://raw.githubusercontent.com/KomodoPlatform/coins/master/utils/coins_config.json"
COINS_CONFIG_PATH = f"{SCRIPT_PATH}/coins_config.json"

COMMIT_HASHES_URL = "https://raw.githubusercontent.com/KomodoPlatform/dPoW/master/README.md"
COMMIT_HASHES_PATH = f"{SCRIPT_PATH}/commit_hashes.json"

SEEDNODE_VERSIONS_URL = "https://raw.githubusercontent.com/KomodoPlatform/dPoW/dev/doc/seed_version_epochs.json"
SEEDNODE_VERSIONS_PATH = f"{SCRIPT_PATH}/seed_versions.json"

# Coins constants
COINS_MAIN = list(set([i['ac_name'] for i in ASSETCHAINS])) + ['GLEEC_OLD']
CONF_PATHS = {
    "main": {
        "KMD": f"{HOME}/.komodo/komodo.conf",
        "LTC": f"{HOME}/.litecoin/litecoin.conf",
        'GLEEC_OLD': f"{HOME}/.komodo/GLEEC_OLD/GLEEC.conf"
    },
    "3p": {
        "KMD_3P": f"{HOME}/.komodo_3p/komodo.conf",
        "TOKEL": f"{HOME}/.komodo_3p/TOKEL/TOKEL.conf",
        "MCL": f"{HOME}/.komodo_3p/MCL/MCL.conf"
    }
}

# Autopopulate conf paths for all main coins
[CONF_PATHS["main"].update({coin: f"{HOME}/.komodo/{coin}/{coin}.conf"}) for coin in COINS_MAIN if coin not in ["KMD", "LTC", "GLEEC_OLD"]]
DPOW_SERVERS = list(CONF_PATHS.keys())
COINS_3P = list(CONF_PATHS["3p"].keys())
DPOW_COINS = COINS_3P + COINS_MAIN + ["KMD", "LTC"]
IMPORT_PRUNED_COINS = ["AYA", "EMC2", "MIL", "CHIPS", "LTC"]
                      
LARGE_UTXO_COINS = ["EMC2", "AYA", "MIL"]

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


IGUANA_CONFIGS = {
    "main": f"{DPOW_PATH}/iguana/elected",
    "3p": f"{DPOW_PATH}/iguana/3rd_party"
}

with open(IGUANA_CONFIGS["main"]) as j:
    _notaries = json.load(j)['notaries']
    PUBKEYS_MAIN = {k: v for d in _notaries for k, v in d.items()}
with open(IGUANA_CONFIGS["3p"]) as j:
    _notaries = json.load(j)['notaries']
    PUBKEYS_3P = {k: v for d in _notaries for k, v in d.items()}

LOG_PATH = f"{HOME}/logs"
if not os.path.exists(LOG_PATH):
    os.makedirs(LOG_PATH)
    
IGUANA_LOGS = {
    "main": f"{LOG_PATH}/iguana_main.log",
    "3p": f"{LOG_PATH}/iguana_3p.log",
}


IGUANA_BIN_MAIN = f"{DPOW_PATH}/iguana/m_notary_main"
IGUANA_BIN_3P = f"{DPOW_PATH}/iguana/m_notary_3rdparty_docker"

# These are not used for anything yet, but will be used in the future to update daemon confs
ADDRESS_WHITELIST = {
    "s6_dragonhound_DEV_main": "RDragoNHdwovvsDLSLMiAEzEArAD3kq6FN",
    "s7_dragonhound_DEV_3p": "RHound8PpyhVLfi56dC7MK3ZvvkAmB3bvQ",
    "s7_dragonhound_DEV_main": "RHi882Amab35uXjqBZjVxgEgmkkMu454KK",
    "s7_dragonhound_DEV_3p": "RLdmqsXEor84FC8wqDAZbkmJLpgf2nUSkq",
    "Notary faucet": "RSzqu1ZmAbbM2WUNdqNtPLTcLB54kwLp6D"
}
# These are not used for anything yet, but will be used in the future to add peers to daemons and iguana
NOTARY_PEERS = {
    "dragonhound_AR": "15.235.204.174",
    "dragonhound_NA": "209.222.101.247",
    "dragonhound_DEV": "103.195.100.32",
    "gcharang_AR": "148.113.1.52",
    "gcharang_SH": "51.161.209.100",
    "gcharang_DEV": "148.113.8.6",
    "Alright_DEV":"144.76.80.75",
    "Alright_EU": "65.21.77.109",
    "Marmara1": "89.19.26.211",
    "Marmara2": "89.19.26.212"
}


# These are not used for anything yet, but will be used in the future to add peers to daemons
ADDNODES = {
    "komodostats": "seed.komodostats.com",
    "webworker": "seed.webworker.sh",
}


INSIGHT_EXPLORERS = {
    "CCL": [
        "https://ccl.komodo.earth/",
        "https://ccl.explorer.dragonhound.info/",
        "https://ccl.kmdexplorer.io/",
        "https://ccl.explorer.dexstats.info/"
    ],
    "CLC": [
        "https://clc.komodo.earth/",
        "https://clc.explorer.dragonhound.info/",
        "https://clc.explorer.dexstats.info/"
    ],
    "GLEEC": [
        "https://explorer.gleec.com/",
        "https://gleec.explorer.dexstats.info/"
    ],
    "GLEEC_OLD": [
        "https://gleec.komodo.earth/",
        "https://gleec.explorer.dragonhound.info/",
        "https://old.gleec.xyz/"
    ],
    "THC": [
        "https://thc.komodo.earth/",
        "https://thc.explorer.dragonhound.info/",
        "https://thc.explorer.dexstats.info/"
    ],
    "ILN": [
        "https://iln.komodo.earth/",
        "https://iln.explorer.dragonhound.info/",
        "https://explorer.ilien.io/",
        "https://iln.explorer.dexstats.info/"
    ],
    "KMD": [
        "https://explorer.komodoplatform.com/",
        "https://explorer.kmd.dev/",
        "https://explorer.kmd.io/",
        "https://kmd.explorer.dexstats.info/",
        "https://kmdexplorer.io/",
        "https://www.kmdexplorer.ru/"
    ],
    "KMD_3P": [
        "https://explorer.komodoplatform.com/",
        "https://explorer.kmd.dev/",
        "https://explorer.kmd.io/",
        "https://kmd.explorer.dexstats.info/",
        "https://kmdexplorer.io/",
        "https://www.kmdexplorer.ru/"
    ],
    "KOIN": [
        "https://koin.komodo.earth/",
        "https://koin.explorer.dragonhound.info/",
        "https://block.koinon.cloud/",
        "https://koin.explorer.dexstats.info/"
    ],
    "MDX": [
        "https://mdx.xpl.monster/"
    ],
    "RAPH": [
        "https://raph.xpl.monster/"
    ],
    "BCZERO": [
        "https://bczero.xpl.monster/"
    ],
    "MCL": [
        "https://mcl.komodo.earth/",
        "https://explorer.marmara.io/",
        "https://mcl.explorer.dexstats.info/",
        "https://mcl.explorer.dragonhound.info/"
    ],
    "NINJA": [
        "https://ninja.komodo.earth/",
        "https://ninja.explorer.dragonhound.info/",
        "https://ninja.explorer.dexstats.info/",
        "https://ninja.kmdexplorer.io/"
    ],
    "PIRATE": [
        "https://pirate.komodo.earth/",
        "https://pirate.explorer.dragonhound.info/",
        "https://explorer.pirate.black/",
        "https://pirate.explorer.dexstats.info/",
        "https://pirate.kmdexplorer.io/"
    ],
    "SUPERNET": [
        "https://supernet.komodo.earth/",
        "https://supernet.explorer.dragonhound.info/",
        "https://supernet.explorer.dexstats.info/",
        "https://supernet.kmdexplorer.io/"
    ],
    "TOKEL": [
        "https://tokel.komodo.earth/",
        "https://tokel.explorer.dragonhound.info/",
        "https://explorer.tokel.io/",
        "https://tokel.explorer.dexstats.info/"
    ]
}

CRYPTOID_API_KEY = os.getenv('CRYPTOID_API_KEY')
CRYPTOID_EXPLORERS = {
}
BLOCKCYPHER_EXPLORERS = {
    'LTC': 'https://api.blockcypher.com/v1/ltc/main'
}
NO_EXPLORER = {
}
WHITELIST_COMPATIBLE = list(set(COINS_MAIN) - set(["LTC"])) + ["KMD_3P", "MCL", "TOKEL", "CHIPS"]

OLD_CONFIG_KEYS = [
    "address_main_kmd", "config_path", "address_main",
    "address_main_ltc", "addresses_3p", "split amount",
    "split_threshold", "split_count"
]

# https://chainz.cryptoid.info/emc2/api.dws?q=unspent&key=f01f30f935a8&active=EeVxpgmmbjLosvkHpmgSjqMFwgvUFCRmeL
# https://api.blockcypher.com/v1/ltc/main/addrs/LS814iSp85xv7N4dGnwAyas92u9AMVr9KV?unspentOnly=true


APP_CONFIG_PATH = f"{SCRIPT_PATH}/config.json"
COINS_NTX_DATA_PATH = f'{SCRIPT_PATH}/coins_ntx_data.json'
# TODO: detect and repair if misconfigured
# use dPoW pubkeys list to populate config for pk and addr etc.



# MM2 constants
MM2_JSON_PATH = os.getenv("MM2_JSON_PATH") or f"{HOME}/notary_docker_3p/mm2/MM2.json"

config = get_cache_data(APP_CONFIG_PATH)
for i in ["whitelist", "addnode", "addnotary"]:
    if i not in config:
        config.update({i: {}})
    if i == "whitelist":
        for k, v in ADDRESS_WHITELIST.items():
            if k not in config[i]:
                config[i].update({k: v})
    if i == "addnode":
        for k, v in ADDNODES.items():
            if k not in config[i]:
                config[i].update({k: v})
    if i == "addnotary":
        for k, v in NOTARY_PEERS.items():
            if k not in config[i]:
                config[i].update({k: v})

with open(APP_CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=4)

for server in CONF_PATHS:
    for coin in CONF_PATHS[server]:
        cf = CONF_PATHS[server][coin]
        if not ".komodo" in cf:
            continue
        whitelisted = []
        addnodes = []
        if os.path.exists(cf):
            with open(cf, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("whitelistaddress"):
                        whitelisted.append(line.split("=")[1].strip().split("#")[0].strip())
                    if line.startswith("addnode"):
                        addnodes.append(line.split("=")[1].strip().split("#")[0].strip())
            with open(cf, "a") as f:
                for k, v in config["whitelist"].items():
                    if v not in whitelisted:
                        f.write(f"whitelistaddress={v} # {k}\n")
                for k, v in config["addnode"].items():
                    if v not in addnodes:
                        f.write(f"addnode={v} # {k}\n")
            # Remove duplicate entries and sort
            with open(cf, "r") as f:
                lines = list(set(f.readlines()))
                lines.sort()
            with open(cf, "w") as f:
                for line in lines:
                    f.write(f"{line}")
