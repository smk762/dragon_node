#!/usr/bin/env python3
import time
import math
import const
import helper
from daemon import DaemonRPC
from logger import logger



def sweep_kmd():
    daemon = DaemonRPC("KMD")
    unspent = daemon.get_unspent()
    logger.info(f"{len(unspent)} unspent utxos detected")
    balance = 0
    for utxo in unspent:
        if utxo["amount"] != 0.00010000 and utxo["spendable"]:
            balance += utxo["amount"]
    logger.info(f"{balance} KMD in non-split UTXOs")
    logger.info(daemon.sendtoaddress(const.SWEEP_ADDR, round(balance-5, 4)))
    

def consolidate_kmd(address, balance):
    daemon = DaemonRPC("KMD")
    daemon.unlock_unspent()
    time.sleep(1)
    txid = ""
    balance = 0
    unspendable = []
    unspent = daemon.get_unspent()
    for i in unspent:
        if i["spendable"]:
            balance += i["amount"]
        else:
            print(f"Unspendable: {i}")
            unspendable.append(i)
    txid = daemon.sendtoaddress(address, math.floor(balance*1000)/1000)
    return unspendable, txid
