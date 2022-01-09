#!/usr/bin/env python3
import lib_atomicdex
import lib_const
import lib_rpc
import lib_tui
import time

for coin in lib_const.DPOW_COINS:
    if coin not in lib_const.IGNORE_COINS:
        launch_params = lib_rpc.get_launch_params(coin)
        lib_rpc.start_chain(coin, launch_params)

        block_height = lib_rpc.wait_for_start(coin, launch_params)

        # get unspent, and if zero, import pk
        unspent = lib_rpc.get_unspent(coin)
        if len(unspent) == 0:
            privkey = lib_atomicdex.get_privkey(coin)
            pk = privkey["result"]["priv_key"]
            tx_history = lib_atomicdex.get_tx_history(coin, 1)["result"]["transactions"]
            if len(tx_history) > 0:
                last_tx = lib_atomicdex.get_tx_history(coin, 1)["result"]["transactions"][0]
                block_height = last_tx["block_height"]
                txid = last_tx["tx_hash"]

            if coin not in ["LTC"] and (CONFIG["server"] == "Main" or coin in ["KMD", "TOKEL", "MCL"]):
                lib_rpc.importprivkey(coin, pk, block_height-1)
                time.sleep(1)
            else:
                lib_rpc.importprivkey(coin, pk)
                time.sleep(1)
                # VRSC does not support import from height or importprunedfunds
                if coin in ["VRSC"]:
                    lib_atomicdex.send_withdraw(coin, 'MAX', lib_helper.get_address(coin))
                else:
                    raw_tx, txoutproof = lib_tui.get_tx_import_info(coin, txid)
                    lib_const.option_print(lib_rpc.importprunedfunds(coin, raw_tx, txoutproof))
                time.sleep(1)