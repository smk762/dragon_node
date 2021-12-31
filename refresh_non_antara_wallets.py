#!/usr/bin/env python3
from lib_tui import refresh_non_antara_wallets

for coin in ["CHIPS", "EMC2", "AYA", "GLEEC-OLD", "SFUSD"]:
	refresh_non_antara_wallet(coin)