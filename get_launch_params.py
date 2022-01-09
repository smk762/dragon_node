#!/usr/bin/env python3
import sys
import lib_rpc
from lib_atomicdex import *

if len(sys.argv) > 1:
    coin = sys.argv[1]
else:
    coins_list = get_enabled_coins_list()
    msg = "Enter coin: "
    option_print(f"Options: {coins_list}")
    coin = get_valid_coin(msg, coins_list)
launch_params = ' '.join(lib_rpc.get_launch_params(coin))
print(launch_params)
