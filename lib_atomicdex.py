#!/usr/bin/env python3
import subprocess
from lib_helper import *


def start_mm2(logfile='mm2_output.log'):
    if not os.path.isfile('mm2'):
        error_print("\nmm2 binary not found in "+SCRIPT_PATH+"!")
        get_mm2("dev")
    mm2_output = open(logfile,'w+')
    subprocess.Popen(["./mm2"], stdout=mm2_output, stderr=mm2_output, universal_newlines=True, preexec_fn=preexec)
    time.sleep(3)
    success_print('{:^60}'.format( "AtomicDEX-API starting."))
    success_print('{:^60}'.format( " Use 'tail -f "+logfile+"' for mm2 console messages."))


def mm2_proxy(params):
    if "coin" in params:
        if params["coin"] == "TOKEL":
            params["coin"] = "TKL"
    params.update({"userpass": MM2_USERPASS})
    #print(json.dumps(params))
    try:
        r = requests.post(MM2_IP, json.dumps(params))
        resp = r.json()
    except requests.exceptions.RequestException as e:
        start_mm2()
        r = requests.post(MM2_IP, json.dumps(params))
        resp = r.json()
        if "error" in resp:
            if resp["error"].find("Userpass is invalid"):
                error_print("MM2 is rejecting your rpc_password. Please check you are not running mm2 or AtomicDEX-Desktop app, and your rpc_password conforms to constraints in https://developers.komodoplatform.com/basic-docs/atomicdex/atomicdex-setup/configure-mm2-json.html#mm2-json")
                sys.exit()
    return resp


def get_activation_command(coin):
    activation_command = None
    if coin == "TOKEL":
        coin = "TKL"
    for protocol in ACTIVATE_COMMANDS:
        if coin in ACTIVATE_COMMANDS[protocol]:
            activation_command = ACTIVATE_COMMANDS[protocol][coin]
    return activation_command



def activate_coins(coins_list, merge_utxo=False):

    for coin in coins_list:
        activated = False
        if coin == "TOKEL":
            coin = "TKL"
        activation_command = get_activation_command(coin)

        if activation_command:
            activation_command.update({
                "tx_history": True
            })
            if merge_utxo:
                activation_command.update({
                    "utxo_merge_params":{
                        "merge_at":100,
                        "check_every":120,
                        "max_merge_at_once":200
                    }
                })

            resp = mm2_proxy(activation_command)

            if "result" in resp:
                status_print(f"{resp['coin']} activated. Balance: {resp['balance']}")

            elif "error" in resp:

                if resp["error"].find("already initialized") >= 0:
                    status_print(f"{coin} was already activated.")
                else:
                    error_print(resp)

            activated = True

        if not activated:
            error_print(f"Activation params not found for {coin}!")




# Documentation: https://developers.komodoplatform.com/basic-docs/atomicdex/atomicdex-api-legacy/my_balance.html
def get_balances_table(coins_list=None, current_prices=None):
    if not coins_list:
        coins_list = get_enabled_coins_list()
    if not current_prices:
        current_prices = requests.get(PRICES_API).json()

    if len(coins_list) == 0:
        status_print("You have no active coins...")
    if len(coins_list) > 0:
        table_print("-"*169)
        table_print('|{:^16s}|{:^24s}|{:^24s}|{:^24s}|{:^58s}|{:^16s}|'.format(
                "Coin",
                "Spendable balance",
                "Unspendable balance",
                "Total balance",
                "Address",
                "USD Value"
            )
        )

        table_print("-"*169)
        total_value = 0
        for coin in coins_list:
            resp = get_balance(coin)
            if 'balance' in resp:
                price = get_price(coin, current_prices)
                total_balance = float(resp['balance']) + float(resp['unspendable_balance'])
                value = round(total_balance * price, 2)
                total_value += value
                table_print('|{:^16s}|{:^24f}|{:^24f}|{:^24f}|{:^58s}|{:^16s}|'.format(
                        coin,
                        float(resp['balance']),
                        float(resp['unspendable_balance']),
                        total_balance,
                        resp['address'],
                        f"${value}"
                    )
                )
            else:
                print(resp)
        table_print("-"*169)
        table_print('{:>151s}|{:^16s}|'.format(
                "Total USD ",
                f"${round(total_value,2)}"
            )
        )
        table_print('{:>151s}{:^16s}'.format(
                "",
                "-"*18)
        )
         

def get_version():
    params = {"method":"version"}
    resp = mm2_proxy(params)
    return resp


def stop_mm2():
    params = {"method":"stop"}
    resp = mm2_proxy(params)
    return resp




def get_enabled_coins_list():
    params = {"method":"get_enabled_coins"}
    enabled_coins = mm2_proxy(params)
    coins_list = []
    if 'error' in enabled_coins:
        error_print(enabled_coins['error'])
    else:
        for item in enabled_coins["result"]:
            coins_list.append(item["ticker"])
    return coins_list


def activate_bot_coins(enabled_coins=False):
    if not enabled_coins:
        enabled_coins = get_enabled_coins_list()
    makerbot_settings = load_makerbot_settings()
    coins_list = list(set(DPOW_COINS) - set(enabled_coins))
    if len(coins_list) > 0:
        success_print("Activating Makerbot coins...")
        activate_coins(DPOW_COINS)


def get_status():
    status_print('{:^80}'.format(
            f"MM2 Version: {get_version()['result']}"
        )
    )


def get_total_balance_usd(enabled_coins=None, current_prices=None):
    if not enabled_coins:
        enabled_coins = get_enabled_coins_list()
    if not current_prices:
        current_prices = requests.get(PRICES_API).json()

    total_balance_usd = 0
    for coin in enabled_coins:
        resp = get_balance(coin)
        if 'balance' in resp:
            price = get_price(coin, current_prices)
            coin_balance = float(resp['balance']) + float(resp['unspendable_balance'])
            total_balance_usd += coin_balance * price
    return round(total_balance_usd,2)


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/my_balance.html
def get_balance(coin):
    return mm2_proxy({"method":"my_balance","coin":coin})


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/my_balance.html
def disable_coin(coin):
    return mm2_proxy({"method":"disable_coin","coin":coin})


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-20/withdraw.html
def withdraw(coin, amount, address):
    if amount == "MAX":
        return mm2_proxy({"mmrpc":"2.0","method":"withdraw","params":{"coin":coin,"to":address,"max":True},"id":0})
    else:
        return mm2_proxy({"mmrpc":"2.0","method":"withdraw","params":{"coin":coin,"to":address,"amount":amount},"id":0})


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/send_raw_transaction.html
def send_raw_tx(coin, tx_hex):
    return mm2_proxy({"method":"send_raw_transaction","coin":coin,"tx_hex":tx_hex})


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/validateaddress.html
def validate_address(coin, address):
    return mm2_proxy({"method":"validateaddress","coin":coin,"address":address})


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/validateaddress.html
def is_address_valid(coin, address):
    return validate_address(coin, address)["result"]["is_valid"]


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/show_priv_key.html
def get_privkey(coin):
    return mm2_proxy({"method":"show_priv_key","coin":coin})


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/show_priv_key.html
def get_tx_history(coin, limit=1):
    return mm2_proxy({"method":"my_tx_history","coin":coin, "limit":limit})


# https://developers.komodoplatform.com/basic-docs/atomicdex-api-legacy/validateaddress.html
def validate_withdraw_amount(amount):
    if amount in ["MAX", "max"]:
        return "MAX"
    else:
        try:
            return float(amount)
        except:
            return False
    

def send_withdraw(coin, amount, address):
    resp = withdraw(coin, amount, address)
    if "error" in resp:
        error_print(resp)
    elif "result" in resp:
        if "tx_hex" in resp["result"]:
            send_resp = send_raw_tx(coin, resp["result"]["tx_hex"])
            if 'tx_hash' in send_resp:
                success_print(f"{amount} {coin} sent to {address}. TXID: {send_resp['tx_hash']}")
                return True
            else:
                error_print(send_resp)
        else:
            error_print(resp)
    else:
        error_print(resp)
    return False

