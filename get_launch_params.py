#!/usr/bin/env python3
import sys
import lib_const
import lib_rpc
import lib_helper
import lib_atomicdex

if len(sys.argv) > 1:
    coin = sys.argv[1]
else:
    coins_list = lib_atomicdex.get_enabled_coins_list()
    msg = "Enter coin: "
    lib_const.option_print(f"Options: {coins_list}")
    coin = lib_helper.get_valid_coin(msg, coins_list)
launch_params = ' '.join(lib_rpc.get_launch_params(coin))
print(launch_params)