#!/usr/bin/env python3
import os
import time
import json
import const
import helper
import requests
import subprocess
import based_58
from color import ColorMsg
from daemon import DaemonRPC
from iguana import Iguana
from configure import Config
from logger import logger


class Notary():
    def __init__(self) -> None:
        self.cfg = Config()
        self.msg = ColorMsg()
        self.config = self.cfg.load()
        self.configured = self.check_config()
        if not self.configured:
            self.cfg.create()
            self.config = self.cfg.load()
        self.addnotary = self.config["addnotary"]
        self.sweep_address = self.config["sweep_address"]

        self.log_path = f"{const.HOME}/logs"
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

    def welcome(self) -> None:
        notary_name = self.get_notary_from_pubkey(self.config[f"pubkey_main"])
        if notary_name != "":
            msg = self.msg.colorize(f"-[{notary_name}]-", "lightgreen")
            print('{:^80}'.format(msg))
    
    def get_notary_from_pubkey(self, pubkey: str) -> str:
        name = ""
        matches_main = [k for k, v in const.PUBKEYS_MAIN.items() if v == pubkey]
        if len(matches_main) > 0:
            name = matches_main[0]
        matches_3p = [k for k, v in const.PUBKEYS_MAIN.items() if v == pubkey]
        if len(matches_3p) > 0:
            name = matches_3p[0]
        if name != "":
            name = name[0].upper() + name[1:]
        return name

    def check_config(self):
        if "pubkey_main" not in self.config:
            return False
        if "pubkey_3p" not in self.config:
            return False
        if "sweep_address" not in self.config:
            return False
        if self.config["pubkey_main"] is None:
            return False
        if self.config["pubkey_3p"] is None:
            return False
        if len(self.config["pubkey_main"]) == 0:
            return False
        if len(self.config["pubkey_3p"]) == 0:
            return False
        return True

    def get_coins_ntx_data(self, refresh=False) -> dict:
        if os.path.exists(const.COINS_NTX_DATA_PATH) and not refresh:
            with open(const.COINS_NTX_DATA_PATH) as file:
                return json.load(file)
        else:
            data = self.get_coins_data()
            with open(const.COINS_NTX_DATA_PATH, "w") as file:
                json.dump(data, file, indent=4)
            return data
        
    def get_utxo_threshold(self, coin: str) -> int:
        coins_ntx_data = self.get_coins_ntx_data()
        if coin in coins_ntx_data:
            return coins_ntx_data[coin]["min_utxo_count"]
        else:
            return coins_ntx_data["KMD"]["min_utxo_count"]
    
    def get_split_amount(self, coin: str) -> int:
        coins_ntx_data = self.get_coins_ntx_data()
        if coin in coins_ntx_data:
            return coins_ntx_data[coin]["split_count"]
        else:
            return coins_ntx_data["KMD"]["split_count"]
        
    def get_utxo_value(self, coin: str, sats=False) -> float:
        coins_ntx_data = self.get_coins_ntx_data()
        if sats:
            factor = 100000000
        else:
            factor = 1
        if coin in coins_ntx_data:
            return coins_ntx_data[coin]["utxo_value"] * factor
        else:
            return coins_ntx_data["KMD"]["utxo_value"] * factor

    def get_coins_data(self) -> dict:
        coins_data = {}
        if not self.configured:
            return coins_data
        for server in const.CONF_PATHS:
            for coin in const.CONF_PATHS[server]:
                coins_data.update({
                    coin: {
                        "conf": const.CONF_PATHS[server][coin],
                        "wallet": helper.get_wallet_path(coin),
                        "utxo_value": helper.get_utxo_value(coin),
                        "utxo_value_sats": helper.get_utxo_value(coin, True),
                        "min_utxo_count": 20,
                        "split_count": 20,
                        "server": server,
                        "address": based_58.get_addr_from_pubkey(
                            self.config[f"pubkey_{server}"],
                            coin
                        ),
                        "txfee": helper.get_tx_fee(coin),
                        "pubkey": self.config[f"pubkey_{server}"]
                    }
                })
        return coins_data
    
    def move_wallet(self, coin: str) -> None:
        if not self.configured:
            return
        try:
            coins_data = self.get_coins_ntx_data()
            now = int(time.time())
            wallet = coins_data[coin]["wallet"]
            wallet_bk = wallet.replace("wallet.dat", f"wallet_{now}.dat")
            os.rename(wallet, wallet_bk)
        except Exception as e:
            logger.error(e)

    def rm_komodoevents(self, coin) -> None:
        if not self.configured:
            return
        coins_data = self.get_coins_ntx_data()
        data_dir = os.path.split(coins_data[coin]["wallet"])
        for filename in ["komodoevents", "komodoevents.ind"]:
            try:
                os.remove(f"{data_dir}{filename}")
            except Exception as e:
                logger.error(e)

    def reset_wallet_all(self) -> None:
        pk = self.msg.input(f"Enter 3P KMD private key: ")
        for coin in const.COINS_3P:
            self.reset_wallet(coin, pk)
        pk = self.msg.input(f"Enter MAIN KMD private key: ")
        for coin in const.COINS_MAIN:
            self.reset_wallet(coin, pk)

    def reset_wallet(self, coin: str, pk=None) -> None:
        # TODO: Add support for 3P coins
        # See https://gist.github.com/DeckerSU/e94386556a7a175f77063e2a73963742
        if coin in ["AYA", "EMC2", "MIL", "CHIPS", "VRSC"]:
            self.msg.status(f"Skipping {coin} reset - these are untested at the moment.")
            return
        daemon = DaemonRPC(coin)
        server = helper.get_coin_server(coin)
        self.move_wallet(coin)
        self.stop(coin)
        self.start(coin)
        # Import wallet without rescan
        if not pk:
            pk = input(f"Enter {server.upper()} KMD private key: ")
        pk = helper.wif_convert(coin, pk)
        daemon.importprivkey(pk, False)
        # Consolidate
        # TODO: This relies on access to explorer APIs, which may not be available for all coins
        # AYA block explorer API has no usable endpoints
        # TODO: Electrums may be a viable alternative
        self.consolidate(coin, True, True)

    def get_vouts(self, coin: str, address: str, value: float) -> dict:
        if coin in ["EMC", "CHIPS", "AYA", "LTC"]:
            fee = helper.get_tx_fee(coin) / 100000000
            if fee == 0:
                fee = 0.0001
            return {address: value - fee}
        else:
            return {address: value}

    def get_utxos(self, coin: str, pubkey: str) -> list:
        daemon = DaemonRPC(coin)
        utxos_data = helper.get_utxos(coin, pubkey)
        if len(utxos_data) == 0:
            try:
                utxos_data = daemon.listunspent()
            except Exception as e:
                logger.error(e)
                return []
        if utxos_data is None:
            return []
        if len(utxos_data) == 0:
            return []
        for i in utxos_data:
            if "amount" not in i:
                if "satoshis" in i:
                    i["amount"] = i["satoshis"] / 100000000
                elif "value" in i:
                    i["amount"] = i["value"] / 100000000
                else:
                    logger.error(f"{coin} UTXO data: {i}")
            
        utxos_data = [i for i in utxos_data if "amount" in i]
        utxos = sorted(utxos_data, key=lambda d: d['amount'], reverse=True)
        return utxos

    def get_inputs(self, utxos: list, exclude_utxos: list, force: bool=False) -> list:
        value = 0
        inputs = []
        for utxo in utxos:
            try:
                # Remap utxo data from APIs
                if "tx_pos" in utxo:
                    utxo["vout"] = utxo["tx_pos"]
                if "tx_hash" in utxo:
                    utxo["txid"] = utxo["tx_hash"]
                if "value" in utxo:
                    utxo["satoshis"] = utxo["value"]

                if {"txid": utxo["txid"], "vout": utxo["vout"]} not in exclude_utxos:
                    if "satoshis" not in utxo:
                        if "amount" in utxo:
                            utxo["satoshis"] = utxo["amount"] * 100000000
                        else:
                            logger.error(f"UTXO has no satoshis: {utxo}")
                    inputs.append({"txid": utxo["txid"], "vout": utxo["vout"]})
                    value += utxo["satoshis"]
                else:
                    logger.debug(f"excluding {utxo['txid']}:{utxo['vout']}")
            except Exception as e:
                logger.debug(e)
                logger.debug(utxo)
        value = round(value/100000000, 8)
        return [inputs, value]
        
    def split_utxos(self, coin: str, force: bool=False) -> None:
        nn = Notary()
        daemon = DaemonRPC(coin)
        unspent = daemon.listunspent()
        utxo_value = helper.get_utxo_value(coin)
        count = daemon.get_utxo_count(utxo_value)
        if count < nn.get_utxo_threshold(coin) or force:
            server = helper.get_coin_server(coin)
            split_amount = nn.get_split_amount(coin)
            sats = int(helper.get_utxo_value(coin, True))
            iguana = Iguana(server)
            if iguana.test_connection():
                r = iguana.splitfunds(coin, split_amount, sats)
                if 'txid' in r:
                    # TODO: explorer link
                    self.msg.darkgrey(f"Split {split_amount} utxos for {coin}: {r['txid']}")
                    daemon.get_explorer_url(r['txid'], 'tx') 
                else:
                    self.msg.darkgrey(f"Error splitting {split_amount} utxos for {coin}: {r}")
            else:
                self.msg.darkgrey(f"Error splitting {split_amount} utxos for {coin}: Iguana not running")
        else:
            self.msg.darkgrey(f"Skipping {coin} ({count} utxos in reserve)")
                
    def consolidate(self, coin: str, reset=False, force: bool=False) -> None:
        print()
        if not self.configured:
            return
        coins_data = self.get_coins_ntx_data()
        address = coins_data[coin]["address"]
        pubkey = coins_data[coin]["pubkey"]
        daemon = DaemonRPC(coin)
        utxos = self.get_utxos(coin, pubkey)
        if len(utxos) == 0:
            logger.warning(f"{coin} No UTXOs found")
            return
        if not reset:
            if len(utxos) < 20 and daemon.getbalance() > 0.001 and not force:
                logger.debug(f"{coin} < 20 UTXOs to consolidate, skipping")
                return

        utxo_chunks = helper.chunkify(utxos, 800)
        for utxos in utxo_chunks:
            inputs_data = self.get_inputs(utxos, [], force)
            inputs = inputs_data[0]
            value = inputs_data[1]
            vouts = self.get_vouts(coin, address, value)
            if len(inputs) > 0 and len(vouts) > 0:
                self.msg.info(f"{coin} consolidating {len(inputs)} UTXOs, value: {value}")
                txid = self.process_raw_transaction(coin, address, utxos, inputs, vouts, force)
                if txid != "":
                    explorer_url = daemon.get_explorer_url(txid, 'tx')
                    if explorer_url != "":
                        txid = explorer_url
                    self.msg.info(f"{coin} Sent {value} to {address}: {txid} from {len(inputs)} input UTXOs")
                else:
                    logger.error(f"{coin} Failed to send {value} to {address} from {len(inputs)} input UTXOs")
                    logger.debug(f"{coin} inputs {inputs}")
                    logger.debug(f"{coin} vouts {vouts}")
                time.sleep(0.1)
            else:
                logger.debug(f"{coin} no valid inputs or vouts for")

    def process_raw_transaction(self, coin: str, address: str, utxos: list, inputs: list, vouts: dict, force=False) -> str:
        daemon = DaemonRPC(coin)
        unsignedhex = daemon.createrawtransaction(inputs, vouts)

        # Some coins dont allow signrawtransaction,
        # others dont have signrawtransactionwithwallet.
        # So we try both
        signedhex = daemon.signrawtransaction(unsignedhex)
        if signedhex is None:
            signedhex = daemon.signrawtransactionwithwallet(unsignedhex)
        if signedhex is None:
            logger.error(f"{coin} Could not signrawtransaction")
            logger.debug(f"{coin} inputs {inputs}")
            logger.debug(f"{coin} vouts {vouts}")
            logger.debug(f"{coin} unsignedhex {unsignedhex}")
            return ""
        time.sleep(0.1)
        txid = daemon.sendrawtransaction(signedhex["hex"])

        if txid is not None:
            return txid
        # Remove error utxos and retry
        if not signedhex['complete']:
            if 'errors' in signedhex:
                errors = signedhex['errors']
                error_utxos = []
                for error in errors:
                    if error['error'] == 'Input not found or already spent':
                        error_utxos.append({"txid": error['txid'], "vout": error['vout']})
                    elif error['error'] == 'Operation not valid with the current stack size':
                        error_utxos.append({"txid": error['txid'], "vout": error['vout']})
                    logger.debug(f"Removing spent utxo: {error['txid']}:{error['error']}")
                if len(error_utxos) == len(inputs):
                    logger.debug(f"All utxos errored, wont send.")
                elif len(error_utxos) > 0:
                    logger.debug(f"Removing {len(error_utxos)} Error UTXOs to try again...")
                    inputs_data = self.get_inputs(utxos, error_utxos, force)
                    inputs = inputs_data[0]
                    value = inputs_data[1]
                    vouts = self.get_vouts(coin, address, value)
                    if len(inputs) > 0 and len(vouts) > 0:
                        try:
                            txid = self.process_raw_transaction(coin, address, utxos, inputs, vouts, force)
                            if txid != "":
                                explorer_url = daemon.get_explorer_url(txid, 'tx')
                                if explorer_url != "":
                                    txid = explorer_url
                                self.msg.info(f"Sent {value} to {address}: {txid}")
                            else:
                                logger.error(f"Failed to send {value} to {address}")
                        except Exception as e:
                            logger.error(e)
                        time.sleep(0.1)
                    else:
                        logger.debug(f"Nothing to send!")
        logger.error(f"{coin} Failed with signedhex {signedhex}")
        logger.error(f"{coin} inputs {inputs}")
        logger.error(f"{coin} vouts {vouts}")
        return ""
                    
    def sweep_kmd(self, coin: str) -> None:
        if not self.configured:
            return
        daemon = DaemonRPC(coin)
        unspent = daemon.listunspent()
        self.msg.info(f"{len(unspent)} unspent utxos detected")
        balance = 0
        for utxo in unspent:
            if utxo["amount"] != 0.00010000 and utxo["spendable"]:
                balance += utxo["amount"]
        if balance > 100:
            self.msg.info(f"{balance} KMD in non-split UTXOs")
            self.msg.info(daemon.sendtoaddress(const.SWEEP_ADDR, round(balance-5, 4)))
        else:
            self.msg.info(f"Only {balance} KMD in non-split UTXOs, skipping sweep.")

    def check_pubkey_files(self, coin: str, docker=True) -> None:
        with open(f"{const.HOME}/dPoW/iguana/pubkey.txt", "r") as f:
            for line in f.readlines():
                if line.startswith(coin):
                    pubkey = line.split("=")[1].strip()
                    break
            
    def restart(self, coin: str, docker=True) -> None:
        self.stop(coin, docker)
        self.start(coin, docker)

    def start(self, coin: str, docker=True) -> None:
        if not self.configured:
            return
        self.start_container(coin)
        self.wait_for_start(coin)

    def stop(self, coin: str, docker=True) -> None:
        if not self.configured:
            return
        # We shouldnt stop a chain until it is ready for RPCs
        self.wait_for_start(coin)
        daemon = DaemonRPC(coin)
        daemon.stop()
        self.wait_for_stop(coin)
        self.stop_container(coin)
        
    def start_container(self, coin):
        coins_data = self.get_coins_ntx_data()
        server = coins_data[coin]["server"]
        if server == "main":
            compose = const.COMPOSE_PATH_MAIN
        else:
            compose = const.COMPOSE_PATH_3P
        try:
            subprocess.run(['docker', 'compose', '-f', compose, 'up', coin.lower(), '-d'], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(e)

    def stop_container(self, coin):
        coins_data = self.get_coins_ntx_data()
        server = coins_data[coin]["server"]
        if server == "main":
            compose = const.COMPOSE_PATH_MAIN
        else:
            compose = const.COMPOSE_PATH_3P
        try:
            subprocess.run(['docker', 'compose', '-f', compose, 'stop', coin.lower()], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(e)

    def wait_for_stop(self, coin: str) -> bool:
        if not self.configured:
            return False
        daemon = DaemonRPC(coin)
        i = 0
        while True:
            try:
                i += 1
                if i == 20:
                    logger.warning(f"Looks like there might be an issue with stopping {coin}...")
                    # TODO: Send an alert if this happens
                    return False
                resp = daemon.is_responding()
                if resp["result"] is None:
                    logger.debug(f"Waiting for {coin} daemon to stop...{resp}")
                    time.sleep(10)
                else:
                    return True
            except Exception as e:
                logger.error(e)
                return True

    def wait_for_start(self, coin: str) -> bool:
        if not self.configured:
            return False
        time.sleep(5)
        daemon = DaemonRPC(coin)
        i = 0
        while True:
            try:
                i += 1
                if i == 180:
                    self.msg.warning(f"Looks like there might be an issue with loading {coin}...")
                    # TODO: Send an alert if this happens
                    return False
                resp = daemon.is_responding()
                if resp["result"] is None:
                    logger.debug(f"Waiting for {coin} daemon to start...{resp}")
                else:
                    return True
            except ConnectionResetError as e:
                logger.debug(f"Waiting for {coin} daemon to start...{e}")
            except Exception as e:
                logger.debug(f"Waiting for {coin} daemon to start...{e}")
            time.sleep(10)
    
    def get_dpow_commit_hashes(self, refresh=False) -> dict:
        if os.path.exists(const.COMMIT_HASHES_PATH) and not refresh:
            with open(const.COMMIT_HASHES_PATH) as file:
                return json.load(file)
        else:
            data = self.parse_dpow_commit_hashes()
            with open(const.COMMIT_HASHES_PATH, "w") as file:
                json.dump(data, file, indent=4)
            return data

    def parse_dpow_commit_hashes(self) -> dict:
        data = {}
        try:
            r = requests.get(const.COMMIT_HASHES_URL)
            for line in r.text.splitlines():
                if len(line) > 0:
                    last_word = line.split()[-1].lower()
                    if last_word in ["dpow-3p", "dpow-mainnet"]:
                        for coin in const.DPOW_COINS:
                            if line.startswith(coin):
                                parts = [i.strip() for i in line.split("|")]
                                commit = parts[2].replace("[", "").split("]")[0]
                                print(f"{coin}: {commit}")
                                data[coin] = commit
                                break
        except Exception as e:
            logger.error(e)
        return data

if __name__ == '__main__':
    nn = Notary()
    nn.get_dpow_commit_hashes(True)