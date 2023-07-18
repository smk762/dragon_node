
#!/usr/bin/env python3
import os
import sys
import csv
import json
import time
import const
import ecdsa
import base58
import string
import codecs
import signal
import hashlib
import secrets
import requests
import binascii
import subprocess
import helper
import based_58
from color import ColorMsg
from insight_api import InsightAPI
from logger import logger


def validate_pubkey(pubkey: str) -> bool:
    # TODO: this is weak validation, improve it
    if len(pubkey) != 66:
        return False
    return True


def get_base58_params():
    url = "https://stats.kmd.io/api/info/base_58/"
    return requests.get(url).json()["results"]

def generate_rpc_pass(length):
    special_chars = "@~-_|():+"
    rpc_chars = string.ascii_letters + string.digits + special_chars
    return "".join(secrets.choice(rpc_chars) for _ in range(length))


def bytes_to_unit(filesize):
    unit = 'B'
    if filesize > 1024:
        unit = 'K'
    if filesize > 1024 ** 2:
        unit = 'M'
    if filesize > 1024 ** 3:
        unit = 'G'
    exponents_map = {'B': 0, 'K': 1, 'M': 2, 'G': 3}
    size = filesize / 1024 ** exponents_map[unit]
    return f"{round(size, 2)}{unit}"


def convert_bytes(num):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def hash160(hexstr):
    preshabin = binascii.unhexlify(hexstr)
    my160 = hashlib.sha256(preshabin).hexdigest()
    return(hashlib.new('ripemd160', binascii.unhexlify(my160)).hexdigest())

def addr_from_ripemd(prefix, ripemd):
    net_byte = prefix + ripemd
    bina = binascii.unhexlify(net_byte)
    sha256a = hashlib.sha256(bina).hexdigest()
    binb = binascii.unhexlify(sha256a)
    sha256b = hashlib.sha256(binb).hexdigest()
    hmmmm = binascii.unhexlify(net_byte + sha256b[:8])
    final = base58.b58encode(hmmmm)
    return(final.decode())

def get_wiftype(coin):
    params = get_base58_params()
    if coin == "KMD_3P":
        coin = "KMD"
    if coin not in params:
        logger.error(f"Coin {coin} not found in base 58 params, using KMD params...")
        return params["KMD"]["wiftype"]
    else:
        return params[coin]["wiftype"]

def validate_wif(pubkey, wif):
    compressed_public_key = helper.wif_to_pubkey(wif)
    if pubkey == compressed_public_key:
        return True
    return False

def wif_decode(compressed_wif):
    b58decode = base58.b58decode(compressed_wif) 
    full_privkey = binascii.hexlify(b58decode) 
    raw_privkey = full_privkey[2:-8]
    private_key = raw_privkey.decode("utf-8")
    return private_key

def private_key_to_public_key(private_key):
    # Hex decoding the private key to bytes using codecs library
    private_key_bytes = codecs.decode(private_key[:-2], 'hex')
    # Generating a public key in bytes using SECP256k1 & ecdsa library
    public_key_raw = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1).verifying_key
    if public_key_raw is not None:
        public_key_bytes = public_key_raw.to_string()
        # Hex encoding the public key from bytes
        public_key_hex = codecs.encode(public_key_bytes, 'hex')
        # Bitcoin public key begins with bytes 0x04 so we have to add the bytes at the start
        public_key = (b'04' + public_key_hex).decode("utf-8")
        return public_key
    return ""

def compress_public_key(public_key):
# Checking if the last byte is odd or even
    if (ord(bytearray.fromhex(public_key[-2:])) % 2 == 0):
        prefix = '02'
    else:
        prefix = '03'
    # Add bytes 0x02 to the X of the key if even or 0x03 if odd
    compressed_public_key = prefix + public_key[2:66]
    return compressed_public_key

def wif_convert(coin, wif):
    raw_privkey = wif_decode(wif)
    wiftype = get_wiftype(coin)
    wiftype_hex = int_to_hexstr(wiftype)
    return WIF_compressed(wiftype_hex, raw_privkey)

def wif_to_pubkey(wif):
    private_key = wif_decode(wif)
    public_key = private_key_to_public_key(private_key)
    compressed_public_key = compress_public_key(public_key)
    return compressed_public_key # AKA pubkey

def uncompressed_public_key_from_private_key(private_key, byte=b'04'):
    # Hex decoding the private key to bytes using codecs library
    private_key_bytes = codecs.decode(private_key, 'hex')
    # Generating a public key in bytes using SECP256k1 & ecdsa library
    public_key_raw = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1).verifying_key
    if public_key_raw is not None:
        public_key_bytes = public_key_raw.to_string()
        # Hex encoding the public key from bytes
        public_key_hex = codecs.encode(public_key_bytes, 'hex')
        # Bitcoin public key begins with bytes 0x04 so we have to add the bytes at the start
        public_key = (byte + public_key_hex).decode("utf-8")
        return public_key
    return ""

def WIF_uncompressed(byte, raw_privkey):
    extended_key = byte+raw_privkey
    first_sha256 = hashlib.sha256(binascii.unhexlify(extended_key[:66])).hexdigest()
    second_sha256 = hashlib.sha256(binascii.unhexlify(first_sha256)).hexdigest()
    # add checksum to end of extended key
    final_key = extended_key[:66]+second_sha256[:8]
    # Wallet Import Format = base 58 encoded final_key
    WIF = base58.b58encode(binascii.unhexlify(final_key))
    return(WIF.decode("utf-8"))

def WIF_compressed(byte, raw_privkey):
    extended_key = byte+raw_privkey+'01'
    first_sha256 = hashlib.sha256(binascii.unhexlify(extended_key[:68])).hexdigest()
    second_sha256 = hashlib.sha256(binascii.unhexlify(first_sha256)).hexdigest()
    # add checksum to end of extended key
    final_key = extended_key[:68]+second_sha256[:8]
    # Wallet Import Format = base 58 encoded final_key
    WIF = base58.b58encode(binascii.unhexlify(final_key))
    return(WIF.decode("utf-8"))


def int_to_hexstr(x):
    if x == 0: return '00'
    hex_chars = '0123456789ABCDEF'
    hex_string = ''
    while x > 0:
        r = x % 16
        hex_string = hex_chars[r] + hex_string
        x = x // 16
    return hex_string


def get_server_coins(server: str) -> list:
    if server == "main":
        return const.COINS_MAIN
    elif server == "3p":
        return const.COINS_3P
    return []


def get_server_pubkey(server):
    with open(const.APP_CONFIG_PATH, "r") as f:
        data = json.load(f)
        if f"pubkey_{server}" in data:
            return data[f"pubkey_{server}"]
        return ""
    


def get_ntx_address(coin):
    if coin in const.NTX_ADDR:
        return const.NTX_ADDR[coin]
    return const.NTX_ADDR["KMD"]


def get_coin_server(coin):
    for server in const.CONF_PATHS:
        if coin in const.CONF_PATHS[server]:
            return server
    return ""

def get_conf_path(coin):
    for server in const.CONF_PATHS:
        if coin in const.CONF_PATHS[server]:
            return const.CONF_PATHS[server][coin]
    return ""

def get_wallet_path(coin: str) -> str:
    for server in const.CONF_PATHS:
        if coin in const.CONF_PATHS[server]:
            conf_path = os.path.split(const.CONF_PATHS[server][coin])[0]
            return f"{conf_path}/wallet.dat"
    return ""

def get_utxos_from_api(coin: str, pubkey: str) -> list:
    address = based_58.get_addr_from_pubkey(pubkey, coin)
    if coin in const.INSIGHT_EXPLORERS:
        baseurl = const.INSIGHT_EXPLORERS[coin]
        if baseurl == "https://chips.explorer.dexstats.info/":
            insight = InsightAPI(baseurl, "api")
        else:
            insight = InsightAPI(baseurl)
        return insight.address_utxos(address)

    elif coin in const.CRYPTOID_EXPLORERS:
        url = f"https://chainz.cryptoid.info/{coin.lower()}/api.dws?q=unspent"
        url += f"&key={const.CRYPTOID_API_KEY}&active={address}"
        r = requests.get(url).json()
        utxos = []
        for i in r["unspent_outputs"]:
            utxos.append({
                "txid": i["tx_hash"],
                "vout": i["tx_ouput_n"],
                "satoshis": i["value"],
                "amount": i["value"] * 100000000
            })
        return utxos

    elif coin in const.BLOCKCYPHER_EXPLORERS:
        url = f"https://api.blockcypher.com/v1/{coin.lower()}/main/addrs/"
        url += f"{address}?unspentOnly=true"
        r = requests.get(url).json()
        utxos = []
        for i in r["txrefs"]:
            utxos.append({
                "txid": i["tx_hash"],
                "vout": i["tx_output_n"],
                "satoshis": i["value"],
                "amount": i["value"] * 100000000
            })
        return utxos

    url = f"http://stats.kmd.io/api/tools/pubkey_utxos/"
    try:
        coin = coin.split("_")[0]
        url += f"?coin={coin}&pubkey={pubkey}"
        logger.info(f"{coin} Getting UTXOs from {url}")
        r = requests.get(url)
        return r.json()["results"]["utxos"]
    except Exception as e:
        if coin in ["AYA", "EMC2", "MIL"]:
            logger.warning(f"{coin} Utxo API not available")
        else:
            logger.error(f"{coin} Error getting UTXOs with pubkey {pubkey}")
            logger.error(e)
        return []


def remap_utxo_data(data):
    utxos = []
    for i in data:
        utxos.append({
            "txid": i["tx_hash"],
            "vout": i["tx_output_n"],
            "satoshis": i["value"],
            "amount": i["value"] * 100000000
        })
    return utxos

def format_param(param, value):
    return '-' + param + '=' + value

def write_json_data(data: object, filename: str) -> None:
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def read_json_data(filename: str) -> dict:
    with open(filename, "r") as f:
        return json.load(f)

def sec_since(ts):
    return int(time.time()) - ts

def sec_to_dhms(sec: int, colorize: bool=True,
                optimal_max: int=7200, lower_threshold: int=21600,
                upper_threshold: int=86400, prefix: str="",
                padding: bool=True, color: bool=True, 
            ) -> str:
    if sec < 0:
        sec = sec*-1
    minutes, seconds = divmod(sec, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    periods = []
    if days > 7:
        return '\033[31m' + " > week!" + '\033[0m'
    elif days > 0:
        periods = [('d', days), ('h', hours)]
    elif hours > 0:
        periods = [('h', hours), ('m', minutes)]
    elif minutes > 0:
        periods = [('m', minutes), ('s', seconds)]
    else:
        periods = [('s', seconds)]
    result = ' '.join('{}{}'.format(int(val), name) for name, val in periods if val)
    if sec < 0:
        result = f"-{result}"
    # Add color and fix padding
    if padding:
        while len(result) < 8:
            result = f" {result}"
    if color:
        if sec < optimal_max:
            result = '\033[92m' + result + '\033[0m'
        if sec > upper_threshold:
            result = '\033[31m' + result + '\033[0m'
        if sec > lower_threshold:
            result = '\033[33m' + result + '\033[0m'
    return result


def get_utxo_value(coin: str, sats=False) -> float:
    if sats:
        factor = 100000000
    else:
        factor = 1
    if coin in const.LARGE_UTXO_COINS:
        return 0.00100000 * factor
    else:
        return 0.00010000 * factor


def get_ntx_stats(wallet_tx, coin):
    last_ntx_time = 0
    last_mined_time = 0
    ntx = []
    ntx_addr = helper.get_ntx_address(coin)
    for tx in wallet_tx:            
        if "address" in tx:
            if tx["address"] == ntx_addr:

                if tx["time"] > last_ntx_time:
                    last_ntx_time = tx["time"]

                if tx["category"] == "send":
                    ntx.append(tx)

            if "generated" in tx:
                if tx["time"] > last_mined_time:
                    last_mined_time = tx["time"]

    ntx_count = len(ntx)
    return [ntx_count, last_ntx_time, last_mined_time]

def get_tx_fee(coin):
    coins_config = get_coins_config()
    if coin in coins_config:
        if "txfee" in coins_config[coin]:
            if coins_config[coin]["txfee"] > 0:
                return coins_config[coin]["txfee"] / 100000000
    if coin in const.LARGE_UTXO_COINS:
        return 0.00010000
    else:
        return 0.00001000


def refresh_external_data(file, url):
    if not os.path.exists(file):
        data = requests.get(url).json()
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    now = int(time.time())
    mtime = os.path.getmtime(file)
    if now - mtime > 21600: # 6 hours
        data = requests.get(url).json()
        with open(file, "w") as f:
            json.dump(data, f, indent=4)
    with open(file, "r") as f:
        return json.load(f)


def get_coins_config():
    return refresh_external_data(const.COINS_CONFIG_PATH, const.COINS_CONFIG_URL)


def get_seednode_versions():
    return refresh_external_data(const.SEEDNODE_VERSIONS_PATH, const.SEEDNODE_VERSIONS_URL)


def get_active_seednode_versions():
    now = int(time.time())
    active_versions = []
    versions = get_seednode_versions()
    for v in versions:
        if versions[v]["end"] > now:
            active_versions.append(v)
    return active_versions

def get_dpow_pubkey(server: str) -> str:
    if server == "main":
        fn = f"{const.HOME}/dPoW/iguana/pubkey.txt"
    elif server == "3p":
        fn = f"{const.HOME}/dPoW/iguana/pubkey_3p.txt"
    else:
        raise ValueError("Invalid server type")
    if not os.path.exists(fn):
        return ""
    pubkey = ""
    with open(fn, "r") as f:
        for line in f.readlines():
            if line.startswith("pubkey"):
                pubkey = line.split("=")[1].strip()
                break
    if not validate_pubkey(pubkey):
        raise ValueError("Invalid pubkey")
    return pubkey

def get_assetchains():
    with open(f"{const.HOME}/dPoW/iguana/assetchains.json") as file:
        return json.load(file)

def input_int(q, min=0, max=1000000000):
    while True:
        try:
            msg = ColorMsg()
            val = msg.input(q)
            if int(val) in range(min, max):
                return int(val)
            else:
                print(f"Invalid input, must be between {min} - {max}. Try again")
        except ValueError:
            print("Invalid input, must be integer. Try again")

def input_coin(q):
    while True:
        msg = ColorMsg()
        valid = const.DPOW_COINS + ["ALL"]
        coin = msg.input(q)
        if coin.upper() in valid:
            return coin
        else:
            print(f"Invalid coin, must be one of {valid}. Try again")


def chunkify(data: list, chunk_size: int):
    return [data[x:x+chunk_size] for x in range(0, len(data), chunk_size)]


def is_configured(config: dict) -> bool:
    if "pubkey_main" not in config:
        return False
    if "pubkey_3p" not in config:
        return False
    if "sweep_address" not in config:
        return False
    if config["pubkey_main"] is None:
        return False
    if config["pubkey_3p"] is None:
        return False
    if len(config["pubkey_main"]) == 0:
        return False
    if len(config["pubkey_3p"]) == 0:
        return False
    return True


# simple key sort
def sort_json_files():
    for i in os.listdir("."):
        if i.endswith(".json"):
            with open(i, "r") as f:
                data = json.load(f)
            with open(i, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)



def convert_csv(file, has_headers=False):
    for i in os.listdir("."):
        if i.endswith(".csv"):
            with open(i, "r") as f:
                csv_reader = csv.DictReader(f)
                line_count = 0
                data = []
                for row in csv_reader:
                    data.append(row)
                    line_count += 1
                print(f'Processed {line_count} lines.')
            with open(i, "w") as f:
                json.dump(data, f, indent=4, sort_keys=True)


def download_progress(url, fn):
    with open(fn, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')

        if total is None:
            f.write(r.content)
        else:
            downloaded = 0
            total = int(total)
            for data in r.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write(f"\rDownloading {fn}: [{'#' * done}{'.' * (50-done)}] {done*2}%")
                sys.stdout.flush()
    sys.stdout.write('\n')
    return r

# Not used in docker env, but left for future reference
def preexec(): # Don't forward signals.
    os.setpgrp()

# Not used in docker env, but left for future reference
def launch(launch_params, log_output):
    subprocess.Popen(launch_params, stdout=log_output, stderr=log_output, universal_newlines=True, preexec_fn=preexec)


def kill_process(process, filter=None):
    try:
        cmd = f"ps ax | grep {process} | grep -v grep"
        if filter:
            cmd += f" | grep {filter}"
        for line in os.popen(cmd):
            fields = line.split()
            pid = fields[0]
            os.kill(int(pid), signal.SIGKILL)
        return "Killed"
    except Exception as e:
        return False
    

if __name__ == '__main__':
    wif = input("Enter WIF: ")
    pubkey = wif_to_pubkey(wif)
    

