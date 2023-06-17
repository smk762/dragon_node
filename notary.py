#!/usr/bin/env python3
import time
import math
import const
import helper
from daemon import DaemonRPC



def sweep_kmd():
    daemon = DaemonRPC("KMD")
    unspent = daemon.get_unspent()
    print(f"{len(unspent)} unspent utxos detected")
    balance = 0
    for utxo in unspent:
        print(utxo)
        #if utxo["amount"] != 0.00010000 and utxo["spendable"]:
        #    balance += utxo["amount"]
    print(f"{balance} KMD in non-split UTXOs")
    print(daemon.sendtoaddress(const.SWEEP_ADDR, round(balance-5, 4)))
    

def consolidate_kmd(address, balance):
    daemon = DaemonRPC("KMD")
    daemon.unlock_unspent()
    time.sleep(1)
    txid = ""
    balance = 0
    unspendable = []
    unspent = daemon.get_unspent()
    for utxo in unspent:
        print(utxo)
        '''
        if utxo["spendable"]:
            balance += utxo["amount"]
        else:
            print(f"Unspendable: {uxto}")
            unspendable.append(utxo)
        '''
    txid = daemon.sendtoaddress(address, math.floor(balance*1000)/1000)
    return unspendable, txid
