#!/usr/bin/env python3
from lib_helper import *
import lib_atomicdex
import lib_rpc


def start_dragonnode():
    coins_list = get_dpow_mainnet_coins()
    lib_atomicdex.activate_coins(coins_list)


def view_balances():
    coins_list = lib_atomicdex.get_enabled_coins_list()
    lib_atomicdex.get_balances_table(coins_list)


def view_stats():
    coins_list = lib_atomicdex.get_enabled_coins_list()
    get_stats_table(coins_list)


def show_launch_params():
    msg = "Enter coin: "
    option_print(f"Options: {DPOW_COINS}")
    coin = get_valid_coin(msg, DPOW_COINS)
    success_print(' '.join(lib_rpc.get_launch_params(coin)))


def show_privkey():
    msg = "Enter coin: "
    option_print(f"Options: {DPOW_COINS}")
    coin = get_valid_coin(msg, DPOW_COINS)
    success_print(get_privkey(coin))


def refresh_wallets():
    max_tx_count = 2000
    for coin in DPOW_COINS:
        try:
            tx_count = lib_rpc.get_wallet_tx_count(coin)
            if tx_count > max_tx_count:
                refresh_wallet(coin)
            else:
                print(f"Skipping {coin}, less than {max_tx_count}")
        except requests.exceptions.RequestException as e:
            print(f"{coin} not responding, skipping...")


def get_min_unspent_conf(unspent):
    minconf = 99999999
    for utxo in unspent:
        if utxo[""] < minconf:
            minconf = utxo["confirmations"]
    return minconf

# AYA did not returna sent txid


def refresh_non_antara_wallet(coin):
    print(f"Resetting {coin}...")
    if coin in ["CHIPS", "EMC2", "AYA", "GLEEC-OLD", "SFUSD"]:
        if coin in LAUNCH_PARAMS:
            if coin in CONFIG["non_antara_addresses"]:
                address = CONFIG["non_antara_addresses"][coin]
                pk = lib_rpc.dumpprivkey(coin,address)
                unspent = lib_rpc.get_unspent(coin)
                balance = lib_rpc.getbalance(coin)
                print(balance)
                txid = lib_rpc.sendtoaddress(coin, address, balance)
                print(txid)
                if txid:
                    # wait for block
                    txoutproof = lib_rpc.gettxoutproof(coin, txid)
                    while not txoutproof:
                        print("Waiting for tx to confirm")
                        time.sleep(20)
                        txoutproof = lib_rpc.gettxoutproof(coin, txid)
                    print(txoutproof)
                    last_block = int(lib_rpc.getblockcount(coin))
                    raw_tx = lib_rpc.getrawtransaction(coin, txid)
                    print(raw_tx)
                    # stop daemon, import pk, import tx
                    print(lib_rpc.stop(coin))

                    lib_rpc.wait_for_stop(coin)

                    # backup wallet.dat
                    ts = int(time.time())
                    data_dir = lib_rpc.get_data_dir(coin)
                    os.popen(f'mv {data_dir}/wallet.dat {data_dir}/wallet_{ts}.dat' )
                    time.sleep(30)

                    # restart chain
                    launch_params = lib_rpc.get_launch_params(coin)
                    lib_rpc.start_chain(coin, launch_params)

                    i = 0
                    while True:
                        try:
                            i += 1
                            if i > 12:
                                print(f"Looks like there might be an issue with loading {coin}... Here are the launch params to do it manually:")
                                print(launch_params)
                            print(f"Waiting for {coin} daemon to restart...")
                            time.sleep(30)
                            block_height = lib_rpc.getblockcount(coin)
                            print(block_height)
                            if block_height:
                                break
                        except:
                            pass
                    time.sleep(20)
                    while last_block == block_height:
                        sleep_message("Waiting for next block...")
                        block_height = lib_rpc.getblockcount(coin)

                    # Import without rescan
                    print(lib_rpc.importprivkey(coin, pk))

                    # Import pruned funds
                    resp = lib_rpc.importprunedfunds(coin, raw_tx, txoutproof)
                    print(resp)


                else:
                    print(f"{coin} did not return a sent txid")
            else:
                print(f"{coin} not in config")
        else:
            print(f"{coin} not in launch_params")
    else:
        print(f"{coin} does not support importprunedfunds")



def refresh_wallet(coin=None):
    if not coin:
        # query coin
        msg = "Enter coin to reset: "
        coin = get_valid_coin(msg, DPOW_COINS)

    if coin in LAUNCH_PARAMS:
        
        # getblockcount
        last_block = int(lib_rpc.getblockcount(coin))

        # get privkey
        address = lib_rpc.get_wallet_addr(coin)
        if address:
            pk = lib_rpc.dumpprivkey(coin,address)
            unspent = lib_rpc.get_unspent(coin)
            lib_rpc.get_unspendable(unspent)
 
            # send to self (use daemon rpc or electrum for non-antara compatible?)
            # create a raw transaction, send after pk without recan import
            if coin in ["LTC", "ARRR", "AYA", "CHIPS", "EMC2", "GLEEC-OLD", "MCL", "SFUSD", "TOKEL", "VRSC"]:
                print(f"Skipping {coin}")
                return
                # lib_rpc.sendtoaddress(coin, address, amount)
            else:
                funds_sent = lib_atomicdex.send_withdraw(coin, 'MAX', address)
                if not funds_sent:
                    return

            time.sleep(10)

            # stop chain
            print(lib_rpc.stop(coin))

            lib_rpc.wait_for_stop(coin)

            # backup wallet.dat
            ts = int(time.time())
            data_dir = lib_rpc.get_data_dir(coin)
            os.popen(f'mv {data_dir}/wallet.dat {data_dir}/wallet_{ts}.dat' )
            time.sleep(30)

            # restart chain
            launch_params = lib_rpc.get_launch_params(coin)
            lib_rpc.start_chain(coin, launch_params)

            i = 0
            while True:
                try:
                    i += 1
                    if i > 12:
                        print(f"Looks like there might be an issue with loading {coin}... Here are the launch params to do it manually:")
                        print(launch_params)
                    print(f"Waiting for {coin} daemon to restart...")
                    time.sleep(30)
                    block_height = lib_rpc.getblockcount(coin)
                    print(block_height)
                    if block_height:
                        break
                except:
                    pass
            time.sleep(20)
            while last_block == block_height:
                sleep_message("Waiting for next block...")
                block_height = lib_rpc.getblockcount(coin)

            #Import using a label and without rescan
            # > einsteinium-cli importprivkey "mykey" "testing" false
            if coin in ["EMC2", "CHIPS", "VRSC", "AYA", "GLEEC-OLD", "SFUSD"]:
                print(lib_rpc.importprivkey(coin, pk))
            else:
                print(lib_rpc.importprivkey(coin, pk, last_block-1))

        else:
            print(f"{coin} has no address!, can't reset")
    else:
        print(f"{coin} not in launch params, can't reset")


def withdraw_funds():
    enabled_coins = lib_atomicdex.get_enabled_coins_list()
    lib_atomicdex.get_balances_table(enabled_coins)
    if len(enabled_coins) > 0:
        coin = color_input("Enter the ticker of the coin you want to withdraw: ")
        while coin not in enabled_coins:
            error_print(f"{coin} is not enabled. Options are |{'|'.join(enabled_coins)}|, try again.")
            coin = color_input("Enter the ticker of the coin you want to withdraw: ")

        amount = color_input(f"Enter the amount of {coin} you want to withdraw, or 'MAX' to withdraw full balance: ")
        amount = lib_atomicdex.validate_withdraw_amount(amount)
        while not amount:
            error_print(f"{amount} is not 'MAX' or a valid numeric value, try again.")
            amount = color_input(f"Enter the amount of {coin} you want to withdraw, or 'MAX' to withdraw full balance: ")    
            amount = lib_atomicdex.validate_withdraw_amount(amount)

        address = color_input(f"Enter the destination address: ")
        while not lib_atomicdex.is_address_valid(coin, address):
            error_print(f"{address} is not a valid {coin} address, try again.")
            address = color_input(f"Enter the destination address: ")
        send_withdraw(coin, amount, address)


def merge_utxos():
    msg = "Enter coin: "
    option_print(f"Options: {DPOW_COINS}")
    coin = get_valid_coin(msg, DPOW_COINS)
    enabled_coins = lib_atomicdex.get_enabled_coins_list()
    if coin in enabled_coins:
        lib_atomicdex.disable_coin(coin)
    lib_atomicdex.activate_coins([coin], True)
    success_print(f"AtomicDEX-API will merge 200 {coin} UTXOs around every 2 minutes until there are less than 250 remaining.")


def loop_views():
    coins_list = get_enabled_coins_list()
    makerbot_params = load_makerbot_params()
    msg = "\nEnter Ctrl-C to exit\n"
    while True:
        try:
            lib_atomicdex.get_balances_table(coins_list)
            sleep_message(msg, 20)
        except KeyboardInterrupt:
            break


def exit_tui():
    msg = "Stop AtomicDEX-API on exit? [Y/N]: "
    valid_options = ["y", "n"]
    q = get_valid_input(msg, valid_options)

    if q.lower() == "y":
        resp = lib_atomicdex.stop_mm2()
        if 'error' in resp:
            error_print(resp)
        elif "success" in resp:
            status_print("AtomicDEX-API has stopped.")
    sys.exit()

