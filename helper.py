
#!/usr/bin/env python3
import sys
import time
import const
import ecdsa
import base58
import string
import codecs
import hashlib
import secrets
import requests
import binascii
import helper
from color import ColorMsg
from logger import logger


def get_launch_params():
    url = "https://stats.kmd.io/api/info/launch_params/"
    launch_params = requests.get(url).json()["results"]
    return launch_params


def get_base58_params():
    url = "https://stats.kmd.io/api/info/base_58/"
    return requests.get(url).json()["results"]
    

def generate_rpc_pass(length):
    special_chars = "@~-_|():+"
    rpc_chars = string.ascii_letters + string.digits + special_chars
    return "".join(secrets.choice(rpc_chars) for _ in range(length))


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
    if coin not in params:
        logger.error(f"Coin {coin} not found in base 58 params")
        sys.exit(1)
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
    public_key_bytes = public_key_raw.to_string()
    # Hex encoding the public key from bytes
    public_key_hex = codecs.encode(public_key_bytes, 'hex')
    # Bitcoin public key begins with bytes 0x04 so we have to add the bytes at the start
    public_key = (b'04' + public_key_hex).decode("utf-8")
    return public_key


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
    public_key_bytes = public_key_raw.to_string()
    # Hex encoding the public key from bytes
    public_key_hex = codecs.encode(public_key_bytes, 'hex')
    # Bitcoin public key begins with bytes 0x04 so we have to add the bytes at the start
    public_key = (byte + public_key_hex).decode("utf-8")
    return public_key
    

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


def get_ntx_address(coin):
    if coin in const.NTX_ADDR:
        return const.NTX_ADDR[coin]
    return const.NTX_ADDR["KMD"]


def get_conf_path(coin):
    for server in const.CONF_PATHS:
        if coin in const.CONF_PATHS[server]:
            return const.CONF_PATHS[server][coin]
    return ""


def sec_since(ts):
    return int(time.time()) - ts


def sec_to_dhms(sec: int, threshold: int=86400) -> str:
    if sec < 0:
        sec = sec*-1
    minutes, seconds = divmod(sec, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    periods = []
    if days > 0:
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
    if sec > threshold:
        result = '\033[31m' + result + '\033[0m'
    return result

def get_utxo_value(coin):
    if coin in const.LARGE_UTXO_COINS:
        utxo_value = 0.00100000
    else:
        utxo_value = 0.00010000

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

if __name__ == '__main__':
    wif = input("Enter WIF: ")
    pubkey = wif_to_pubkey(wif)
    

