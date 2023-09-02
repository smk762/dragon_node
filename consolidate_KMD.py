#!/usr/bin/env python3
from notary import Notary
from daemon import DaemonRPC
from helper import get_ntx_stats, sec_since

notary = Notary()
for coin in ["KMD", "KMD_3P"]:
    rpc = DaemonRPC(coin)
    wallet_tx = rpc.listtransactions()
    stats = get_ntx_stats(wallet_tx, coin)
    sec_since = sec_since(stats[1])
    if sec_since > 3600:
        notary.consolidate(coin, True, True)
