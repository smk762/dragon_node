#!/usr/bin/env python3
from lib_atomicdex import *
import lib_rpc


def start_dragonnode():
    coins_list = get_dpow_mainnet_coins()
    activate_coins(coins_list)


def view_balances():
    coins_list = get_enabled_coins_list()
    get_balances_table(coins_list)


def view_stats():
    coins_list = get_enabled_coins_list()
    get_stats_table(coins_list)


def refresh_wallet():
    # query coin
    msg = "Enter coin to reset: "
    coin = get_valid_coin(msg, DPOW_MAIN_COINS)
    # getblockcount
    print(lib_rpc.rpc_proxy(coin, "listaddressgroupings"))
    block_height = lib_rpc.rpc_proxy(coin, "getblockcount")
    print(block_height)
    # get address
    # get privkey
    # stop chain
    # bacup wallet.dat
    # restart chain
    # import key at blockheight
    # use mm2 to send funds to self (wrt to coinbase maturity)



def exit_tui():
    msg = "Stop AtomicDEX-API on exit? [Y/N]: "
    valid_options = ["y", "n"]
    get_valid_input(msg, valid_options)

    if q.lower() == "y":
        resp = stop_mm2()
        if 'error' in resp:
            error_print(resp)
        elif "success" in resp:
            status_print("AtomicDEX-API has stopped.")
    sys.exit()

