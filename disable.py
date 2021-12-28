#!/usr/bin/env python3
from lib_atomicdex import *

coins_list = get_enabled_coins_list()
msg = "Enter coin: "
option_print(f"Options: {coins_list}")
coin = get_valid_coin(msg, coins_list)
disable_coin(coin)