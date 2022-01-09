#!/usr/bin/env python3
import lib_const
import lib_rpc

for coin in lib_const.DPOW_COINS:
    if coin not in lib_const.IGNORE_COINS:
        launch_params = lib_rpc.get_launch_params(coin)
        lib_rpc.start_chain(coin, launch_params)
