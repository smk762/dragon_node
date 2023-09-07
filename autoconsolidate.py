#!/usr/bin/env python3
from notary import Notary
from daemon import DaemonRPC
from const import COINS_3P, COINS_MAIN, IMPORT_PRUNED_COINS
from helper import sec_since

notary = Notary()
coins = COINS_3P + COINS_MAIN
coins = [coin for coin in coins if coin not in IMPORT_PRUNED_COINS]

for coin in coins:
    rpc = DaemonRPC(coin)
    last_tx = rpc.listtransactions(1)[0]["time"]
    since = sec_since(last_tx)

    # If no KMD notas for > 4 hours, consolidate
    if coin in ["KMD"] and since > 3600 * 4:
        notary.consolidate(coin, True, True)
    # If no 3P KMD notas for > 8 hours, consolidate
    elif coin in ["KMD_3P"] and since > 3600 * 6:
        notary.consolidate(coin, True, True)
    # If no transactions for > 12 hours, consolidate
    elif since > 3600 * 12:
        notary.consolidate(coin, True, True)
