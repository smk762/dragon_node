#!/usr/bin/env python3
import requests
from lib_tui import refresh_non_antara_wallet

max_tx_count = 2000
for coin in ["CHIPS", "EMC2", "AYA", "GLEEC-OLD", "SFUSD"]:
    try:
        tx_count = lib_rpc.get_wallet_tx_count(coin)
        if tx_count > max_tx_count:
            refresh_non_antara_wallet(coin)
        else:
            print(f"Skipping {coin}, less than {max_tx_count}")
    except requests.exceptions.RequestException as e:
        print(f"{coin} not responding, skipping...")
	