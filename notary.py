#!/usr/bin/env python3
import os
import time
import json
import const
import helper
import requests
import subprocess
from color import ColorMsg
from daemon import DaemonRPC
from iguana import Iguana
from configure import Config
from logger import logger


class Notary():
    def __init__(self) -> None:
        self.cfg = Config()
        self.msg = ColorMsg()
  
    def welcome(self) -> None:
        config = self.cfg.load()
        notary_name = self.get_notary_from_pubkey(config["pubkey_main"])
        if notary_name != "":
            msg = self.msg.colorize(f"-[{notary_name}]-", "lightgreen")
        else:
            msg = self.msg.colorize(f"-[ Not configured! ]-", "lightred")
        print('{:^90}'.format(msg))
    
    def get_notary_from_pubkey(self, pubkey: str) -> str:
        name = ""
        matches_main = [k for k, v in const.PUBKEYS_MAIN.items() if v == pubkey]
        if len(matches_main) > 0:
            name = matches_main[0]
        matches_3p = [k for k, v in const.PUBKEYS_3P.items() if v == pubkey]
        if len(matches_3p) > 0:
            name = matches_3p[0]
        if name != "":
            name = name[0].upper() + name[1:]
        return name

        
    def get_utxo_threshold(self, coin: str) -> int:
        coins_ntx_data = self.cfg.get_coins_ntx_data()
        if coin in coins_ntx_data:
            if "split_threshold" in coins_ntx_data[coin]:
                return coins_ntx_data[coin]["split_threshold"]
        else:
            if "split_threshold" in coins_ntx_data["KMD"]:
                return coins_ntx_data["KMD"]["split_threshold"]
        return 20
    
    def get_split_amount(self, coin: str) -> int:
        coins_ntx_data = self.cfg.get_coins_ntx_data()
        if coin in coins_ntx_data:
            # Temporary fix for coins that have split_count instead of split_amount
            # TODO: remove later
            if "split_count" in coins_ntx_data[coin]:
                return coins_ntx_data[coin]["split_count"]
            if "split_amount" in coins_ntx_data[coin]:
                return coins_ntx_data[coin]["split_amount"]
            return 20
        else:
            coin = "KMD"
            if "split_count" in coins_ntx_data[coin]:
                return coins_ntx_data[coin]["split_count"]
            if "split_amount" in coins_ntx_data[coin]:
                return coins_ntx_data[coin]["split_amount"]
            return 20
        
    def get_utxo_value(self, coin: str, sats=False) -> float:
        coins_ntx_data = self.cfg.get_coins_ntx_data()
        if sats:
            factor = 100000000
        else:
            factor = 1
        if coin in coins_ntx_data:
            return coins_ntx_data[coin]["utxo_value"] * factor
        else:
            return coins_ntx_data["KMD"]["utxo_value"] * factor

    
    def move_wallet(self, coin: str) -> None:
        config = self.cfg.load()
        if helper.is_configured(config):
            try:
                coins_data = self.cfg.get_coins_ntx_data()
                now = int(time.time())
                wallet = coins_data[coin]["wallet"]
                wallet_bk = wallet.replace("wallet.dat", f"wallet_{now}.dat")
                os.rename(wallet, wallet_bk)
            except Exception as e:
                logger.error(e)

    def rm_komodoevents(self, coin) -> None:
        config = self.cfg.load()
        if helper.is_configured(config):
            coins_data = self.cfg.get_coins_ntx_data()
            data_dir = os.path.split(coins_data[coin]["wallet"])
            for filename in ["komodoevents", "komodoevents.ind"]:
                try:
                    os.remove(f"{data_dir}{filename}")
                except Exception as e:
                    logger.error(e)

    def reset_wallet_all(self, exclude_noconsolidate: bool=True) -> None:
        pk = self.msg.input(f"Enter 3P KMD private key: ")
        for coin in const.COINS_3P:
            self.reset_wallet(coin, pk)
        pk = self.msg.input(f"Enter MAIN KMD private key: ")
        for coin in const.COINS_MAIN:
            self.reset_wallet(coin, pk)

    def reset_wallet(self, coin: str, pk=None, exclude_noconsolidate: bool=True) -> None:
        # TODO: Add support for 3P coins
        # See https://gist.github.com/DeckerSU/e94386556a7a175f77063e2a73963742
        if coin in const.IMPORT_PRUNED_COINS:
            if exclude_noconsolidate:
                self.msg.status(f"Skipping {coin} reset - these are untested at the moment.")
                return
            else:
                ref_url = "https://gist.github.com/DeckerSU/e94386556a7a175f77063e2a73963742"
                self.msg.status(f"{coin} will not auto-consolidate!")
                self.msg.status(f"See {ref_url} for notes about cleaning this coin.")
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
        self.consolidate(coin, True)

    def get_vouts(self, coin: str, address: str, value: float, tx_size: int) -> dict:
        fee = 0
        if coin in ["LTC"]:
            fee = tx_size * 0.00000002
        elif coin in ["EMC", "CHIPS", "AYA"]:
            if coin in const.LARGE_UTXO_COINS:
                fee = 0.00010000
            else:
                fee = 0.00001000
        self.msg.darkgrey(f"{coin} fee: {fee}")
        return {address: value - fee}

    def get_utxos(self, coin: str, pubkey: str, api=True) -> list:
        daemon = DaemonRPC(coin)
        if api:
            utxos_data = helper.get_utxos_from_api(coin, pubkey)
        else:
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
                if {"txid": utxo["txid"], "vout": utxo["vout"]} not in exclude_utxos:
                    inputs.append({"txid": utxo["txid"], "vout": utxo["vout"]})
                    value += utxo["satoshis"]
                else:
                    logger.debug(f"excluding {utxo['txid']}:{utxo['vout']}")
            except Exception as e:
                logger.debug(e)
                logger.debug(utxo)
        value = round(value/100000000, 8)
        return [inputs, value]
        
    def split_utxos(self, coin: str, force: bool=False) -> bool:
        daemon = DaemonRPC(coin)
        unspent = daemon.listunspent()
        utxo_value = helper.get_utxo_value(coin)
        count = daemon.get_utxo_count(utxo_value)
        if count < self.get_utxo_threshold(coin) or force:
            server = helper.get_coin_server(coin)
            split_amount = self.get_split_amount(coin)
                
            sats = int(helper.get_utxo_value(coin, True))
            iguana = Iguana(server)
            if iguana.test_connection():
                r = iguana.splitfunds(coin, split_amount, sats)
                if 'error' in r:
                    iguana.addcoin(coin)
                    time.sleep(0.1)
                    iguana.dpow(coin)
                    time.sleep(0.1)
                    r = iguana.splitfunds(coin, split_amount, sats)
                if 'txid' in r:
                    # TODO: explorer link
                    self.msg.green(f"Split {split_amount} utxos for {coin}: {r['txid']}")
                    link = daemon.get_explorer_url(r['txid'], 'tx') 
                    if link != "":
                        self.msg.ltcyan(f"Explorer: {link}")
                    return True
                else:
                    self.msg.darkgrey(f"Error splitting {split_amount} utxos for {coin}: {r}")
                    return False
            else:
                self.msg.darkgrey(f"Error splitting {split_amount} utxos for {coin}: Iguana not running")
                return False
        else:
            self.msg.darkgrey(f"Skipping {coin} ({count} utxos in reserve)")
            return True
                
    def consolidate(self, coin: str, force: bool=False, api: bool=False) -> None:
        config = self.cfg.load()
        if helper.is_configured(config):
            print()
            daemon = DaemonRPC(coin)
            coins_data = self.cfg.get_coins_ntx_data()
            address = coins_data[coin]["address"]
            pubkey = coins_data[coin]["pubkey"]
            utxos = self.get_utxos(coin, pubkey, api)
            if len(utxos) == 0:
                logger.warning(f"{coin} No UTXOs found")
                return
            if not force:
                if len(utxos) < 5 and daemon.getbalance() > 0.001 and not force:
                    logger.debug(f"{coin} < 5 UTXOs to consolidate, skipping")
                    return

            utxo_chunks = helper.chunkify(utxos, 800)
            for utxos in utxo_chunks:
                inputs_data = self.get_inputs(utxos, [], force)
                inputs = inputs_data[0]
                # Assuming 100 bytes per input
                tx_size = len(inputs) * 100
                value = inputs_data[1]
                vouts = self.get_vouts(coin, address, value, tx_size)
                if len(inputs) > 0 and len(vouts) > 0:
                    self.msg.darkgrey(f"{coin} consolidating {len(inputs)} UTXOs, value: {value}")
                    txid = self.process_raw_transaction(coin, address, utxos, inputs, vouts, force)
                    if txid != "":
                        explorer_url = daemon.get_explorer_url(txid, 'tx')
                        if explorer_url != "":
                            txid = explorer_url
                        self.msg.ltgreen(f"{coin} Sent {value} to {address}: {txid} from {len(inputs)} input UTXOs")
                    else:
                        logger.error(f"{coin} Failed to send {value} to {address} from {len(inputs)} input UTXOs")
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
                    tx_size = len(inputs) * 100
                    vouts = self.get_vouts(coin, address, value, tx_size)
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
                    
    def sweep_kmd(self) -> None:
        config = self.cfg.load()
        if helper.is_configured(config):
            daemon = DaemonRPC("KMD")
            unspent = daemon.listunspent()
            self.msg.info(f"{len(unspent)} unspent utxos detected")
            balance = 0
            for utxo in unspent:
                if utxo["amount"] != 0.00010000 and utxo["spendable"]:
                    balance += utxo["amount"]
            if balance > 500:
                self.msg.info(f"{balance} KMD in non-split UTXOs")
                self.msg.info(daemon.sendtoaddress(config["sweep_address"], round(balance-5, 4)))
            else:
                self.msg.info(f"Only {balance} KMD in non-split UTXOs, skipping sweep.")
            
    def restart(self, coin: str, docker=True) -> None:
        self.stop(coin, docker)
        self.start(coin, docker)

    def start(self, coin: str, docker=True) -> None:
        self.start_container(coin)
        self.wait_for_start(coin)

    def stop(self, coin: str, docker=True) -> None:
        # We shouldnt stop a chain until it is ready for RPCs
        self.wait_for_start(coin)
        daemon = DaemonRPC(coin)
        daemon.stop()
        self.wait_for_stop(coin)
        self.stop_container(coin)
        
    def start_container(self, coin):
        config = self.cfg.load()
        if helper.is_configured(config):
            coins_data = self.cfg.get_coins_ntx_data()
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
        config = self.cfg.load()
        if helper.is_configured(config):
            coins_data = self.cfg.get_coins_ntx_data()
            server = coins_data[coin]["server"]
            if server == "main":
                compose = const.COMPOSE_PATH_MAIN
            else:
                compose = const.COMPOSE_PATH_3P
            try:
                subprocess.run(['docker', 'compose', '-f', compose, 'stop', coin.lower()], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(e)

    def wait_for_stop(self, coin: str):
        config = self.cfg.load()
        if helper.is_configured(config):
            daemon = DaemonRPC(coin)
            i = 0
            while True:
                try:
                    i += 1
                    if i == 30:
                        # TODO: Send an alert if this happens
                        logger.warning(f"Looks like there might be an issue with stopping {coin}...")
                    resp = daemon.is_responding()
                    if resp["result"] is None:
                        logger.debug(f"Waiting for {coin} daemon to stop...{resp}")
                        time.sleep(10)
                except Exception as e:
                    logger.error(e)
        else:
            logger.debug(f"App not configured, skipping...")

    def wait_for_start(self, coin: str):
        config = self.cfg.load()
        if helper.is_configured(config):
            time.sleep(5)
            daemon = DaemonRPC(coin)
            i = 0
            while True:
                try:
                    i += 1
                    if i == 180:
                        # TODO: Send an alert if this happens
                        self.msg.warning(f"Looks like there might be an issue with loading {coin}...")
                    resp = daemon.is_responding()
                    if resp["result"] is None:
                        logger.debug(f"Waiting for {coin} daemon to start...{resp}")
                except ConnectionResetError as e:
                    logger.debug(f"Waiting for {coin} daemon to start...{e}")
                except Exception as e:
                    logger.debug(f"Waiting for {coin} daemon to start...{e}")
                time.sleep(10)
        else:
            logger.debug(f"App not configured, skipping...")
    
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