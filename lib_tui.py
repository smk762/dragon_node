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
    coin = get_valid_coin(msg, DPOW_COINS)
    success_print(' '.join(lib_rpc.get_launch_params(coin)))


def show_privkey():
    msg = "Enter coin: "
    option_print(f"Options: {DPOW_COINS}")
    coin = get_valid_coin(msg, DPOW_COINS)
    success_print(get_privkey(coin))


def get_min_unspent_conf(unspent):
    minconf = 99999999
    for utxo in unspent:
        if utxo[""] < minconf:
            minconf = utxo["confirmations"]
    return minconf


def refresh_wallets():
    for coin in DPOW_COINS:
        try:
            refresh_wallet(coin)
        except requests.exceptions.RequestException as e:
            print(f"{coin} not responding, skipping...")


def refresh_wallet(coin=None):
        
    if not coin:
        # query coin
        msg = "Enter coin to reset: "
        coin = get_valid_coin(msg, DPOW_COINS)

    print(f"Refreshing {coin} wallet")

    max_tx_count = 2000
    tx_count = lib_rpc.get_wallet_tx_count(coin)
    if tx_count < max_tx_count:
        print(f"Skipping {coin}, less than {max_tx_count}")
        return False

    launch_params = lib_rpc.get_launch_params(coin)
    if not launch_params:
        print(f"unable to launch_params")
        return False

    # get address 
    if coin in CONFIG["non_antara_addresses"]:
        address = CONFIG["non_antara_addresses"][coin]
    else:
        address = lib_helper.addr_from_pubkey(coin, CONFIG["pubkey"])

    if not address:            
        print(f"unable to get address")
        return

    # getblockcount
    data_dir = lib_rpc.get_data_dir(coin)
    print(f"data_dir: {data_dir}")
    last_block = int(lib_rpc.getblockcount(coin))
    print(f"last_block: {last_block}")
    pk = lib_rpc.dumpprivkey(coin,address)
    balance = lib_rpc.getbalance(coin)
    print(f"balance: {balance}")

    txid = lib_rpc.sendtoaddress(coin, address, balance)
    if not txid:
        print(f"unable to get txid")
        return False
    print(f"txid: {txid}")
    
    if coin in IMPORT_PRUNED_COINS:
        txoutproof, raw_tx = get_tx_import_info(coin, txid)
        if not txoutproof or not raw_tx:
            print(f"unable to get txoutproof and/or raw_tx")
            return False

    time.sleep(10)

    # stop chain
    print(lib_rpc.stop(coin))
    lib_rpc.wait_for_stop(coin)
    time.sleep(10)

    #backup wallet
    backup_wallet_dat(data_dir)
    time.sleep(30)

    # restart chain
    lib_rpc.start_chain(coin, launch_params)
    block_height = lib_rpc.wait_for_start(coin, launch_params)
    print(f"block_height: {block_height}")
    time.sleep(20)

    while last_block == block_height:
        sleep_message("Waiting for next block...")
        block_height = lib_rpc.getblockcount(coin)
        print(f"block_height: {block_height}")


    if CONFIG["server"] == "Main" or coin in ["KMD", "TOKEL", "MCL"]:
        print(lib_rpc.importprivkey(coin, pk, last_block-1))
        time.sleep(1)
    else:
        print(lib_rpc.importprivkey(coin, pk))
        time.sleep(1)
        print(lib_rpc.importprunedfunds(coin, raw_tx, txoutproof))
        time.sleep(1)

    # does not support import from height or importprunedfunds
    if coin in ["VRSC"]:
        lib_atomicdex.send_withdraw(coin, amount, 'MAX')

    return lib_rpc.getbalance(coin)
        

def backup_wallet_dat(data_dir):
    # backup wallet.dat
    ts = int(time.time())
    backup_wallet = f"{data_dir}/wallet_{ts}.dat"
    os.popen(f'mv {data_dir}/wallet.dat {backup_wallet}')
    print(f"Backup wallet saved as {backup_wallet}")




def get_tx_import_info(coin, txid):
    txoutproof = lib_rpc.gettxoutproof(coin, txid)
    i = 0
    while not txoutproof:
        print("Waiting for tx to confirm")
        time.sleep(20)
        txoutproof = lib_rpc.gettxoutproof(coin, txid)
        i += 1
        if i > 15:
            return False, False
    raw_tx = lib_rpc.getrawtransaction(coin, txid)
    return txoutproof, raw_tx


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
        lib_atomicdex.send_withdraw(coin, amount, address)


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

