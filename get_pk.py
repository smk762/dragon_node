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

pk = lib_atomicdex.get_privkey(coin)
print(pk)

