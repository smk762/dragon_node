#!/usr/bin/env python3
import os
import time
import const
import helper
import subprocess
from daemon import DaemonRPC
from configure import Config
from logger import logger


class Notary():
    def __init__(self) -> None:
        self.config = Config().load()
        self.configured = self.check_config()
        if self.configured is False:
            return
        self.addnotary = self.config["addnotary"]
        self.sweep_address = self.config["sweep_address"]
        self.coins_data = self.get_coins_data()
        self.log_path = f"{const.HOME}/logs"
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

    def check_config(self):
        if "pubkey_main" not in self.config:
            return False
        if "pubkey_3p" not in self.config:
            return False
        if "sweep_address" not in self.config:
            return False
        return True

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
                        "daemon": DaemonRPC(coin),
                        "utxo_value": helper.get_utxo_value(coin),
                        "min_utxo_count": 20,
                        "split_count": 20,
                        "server": server,
                        "launch_params": server,
                        "pubkey": self.config[f"pubkey_{server}"]
                    }
                })
                if server == "main":
                    coins_data[coin].update({
                        "address": self.config[f"address_main"],
                })
                else:
                    coins_data[coin].update({
                        "address": self.config[f"addresses_3p"][coin.replace("_3P", "")],
                })
        return coins_data
    
    def move_wallet(self, coin: str) -> None:
        if not self.configured:
            return
        try:
            now = int(time.time())
            wallet = self.coins_data[coin]["wallet"]
            wallet_bk = wallet.replace("wallet.dat", f"wallet_{now}.dat")
            os.rename(wallet, wallet_bk)
        except Exception as e:
            logger.error(e)

    def rm_komodoevents(self, coin) -> None:
        if not self.configured:
            return
        data_dir = os.path.split(self.coins_data[coin]["wallet"])
        for filename in ["komodoevents", "komodoevents.ind"]:
            try:
                os.remove(f"{data_dir}{filename}")
            except Exception as e:
                logger.error(e)

    def reset_wallet(self, coin: str) -> None:
        if coin in ["AYA", "EMC2", "MIL", "CHIPS", "VRSC"]:
            logger.info(f"Skipping {coin} reset - these are untested at the moment.")
        daemon = DaemonRPC(coin)
        server = helper.get_coin_server(coin)
        # Backup wallet
        self.move_wallet(coin)
        # Stop coin
        self.stop(coin)
        # Restart coin
        self.start(coin)
        # Import wallet without rescan
        pk = input(f"Enter {server.upper()} KMD private key: ")
        pk = helper.wif_convert(coin, pk)
        daemon.importprivkey(pk, False)
        # Consolidate
        # TODO: This relies on access to explorer APIs, which may not be available for all coins
        # TODO: Electrums may be a viable alternative
        self.consolidate(coin, True)

    def get_vouts(self, coin: str, address: str, value: float) -> dict:
        value = round(value/100000000, 8)
        if coin in ["EMC", "CHIPS", "AYA"]:
            # Got -26 error if not reducing amount
            return {address: value - 0.001}
        else:
            return {address: value}

    def get_utxos(self, coin: str, pubkey: str) -> list:
        daemon = DaemonRPC(coin)
        utxos_data = helper.get_utxos(coin, pubkey)
        if len(utxos_data) == 0:
            try:
                utxos_data = daemon.listunspent()
            except Exception as e:
                logger.error(f"Error getting UTXOs for {coin}: e")
                return []
        utxos = sorted(utxos_data, key=lambda d: d['amount'], reverse=True)
        if len(utxos) > 0:
            logger.info(f"Biggest {coin} UTXO: {utxos[0]['amount']}")
            logger.info(f"{len(utxos)} {coin} UTXOs")
        return utxos

    def get_inputs(self, utxos: list, exclude_utxos: list) -> list:
        value = 0
        inputs = []
        for utxo in utxos:
            if {"txid": utxo["txid"], "vout": utxo["vout"]} not in exclude_utxos:
                # for daemon resp data
                if "satoshis" not in utxo:
                    utxo["satoshis"] = utxo["amount"] * 100000000
                if utxo["confirmations"] < 100:
                        continue
                inputs.append({"txid": utxo["txid"], "vout": utxo["vout"]})
                value += utxo["satoshis"]
        return [inputs, value]
        

    def consolidate(self, coin: str, reset=False) -> None:
        if not self.configured:
            return
        address = self.coins_data[coin]["address"]
        pubkey = self.coins_data[coin]["pubkey"]
        daemon = self.coins_data[coin]["daemon"]
        utxos = self.get_utxos(coin, pubkey)
        if not len(utxos) == 0:
            logger.warning(f"No UTXOs found for {coin}")
            return
        if not reset:
            if len(utxos) < 20 and daemon.getbalance() > 0.001:
                logger.debug(f"< 20 UTXOs to consolidate {coin}, skipping")
                return

        logger.info(f"consolidating {coin}...")
        utxo_chunks = helper.chunkify(utxos, 800)
        for utxos in utxo_chunks:
            inputs_data = self.get_inputs(utxos, [])
            inputs = inputs_data[0]
            value = inputs_data[1]
            vouts = self.get_vouts(coin, address, value)
            logger.info(f"consolidating {len(inputs)} UTXOs, value: {value}")
            try:
                txid = self.process_raw_transaction(coin, address, utxos, inputs, vouts)
                logger.info(f"Sent {value} to {address}: {txid}")
            except Exception as e:
                logger.error(e)
            time.sleep(1)

    def process_raw_transaction(self, coin: str, address: str, utxos: list, inputs: list, vouts: dict) -> str:
        daemon = DaemonRPC(coin)
        unsignedhex = daemon.createrawtransaction(inputs, vouts)
        # logger.debug(f"unsignedhex: {unsignedhex}")
        time.sleep(0.1)
        if coin in ["AYA"]:
            signedhex = daemon.signrawtransactionwithwallet(unsignedhex)
        else:
            signedhex = daemon.signrawtransaction(unsignedhex)
        # logger.debug(f"signedhex: {signedhex}")
        time.sleep(0.1)
        txid = daemon.sendrawtransaction(signedhex["hex"])
        if txid is not None:
            # TODO: add explorer URL
            logger.info(f"txid: {txid}")
            return txid
        else:
            # TODO: we should be able to remove the error utxo and retry here
            if not signedhex['complete']:
                errors = signedhex['errors']
                error_utxos = []
                for error in errors:
                    if error['error'] == 'Input not found or already spent':
                        error_utxos.append({"txid": error['txid'], "vout": error['vout']})
                    else:
                        logger.error(f"{error['error']}")
                if len(error_utxos) > 0:
                    inputs_data = self.get_inputs(utxos, error_utxos)
                    inputs = inputs_data[0]
                    value = inputs_data[1]
                    vouts = self.get_vouts(coin, address, value)
                    logger.info(f"consolidating {len(inputs)} UTXOs, value: {value}")
                    try:
                        txid = self.process_raw_transaction(coin, address, utxos, inputs, vouts)
                        logger.info(f"Sent {value} to {address}: {txid}")
                    except Exception as e:
                        logger.error(e)
        return ""
                    
    def sweep_kmd(self, coin: str) -> None:
        if not self.configured:
            return
        daemon = self.coins_data[coin]["daemon"]
        unspent = daemon.listunspent()
        logger.info(f"{len(unspent)} unspent utxos detected")
        balance = 0
        for utxo in unspent:
            if utxo["amount"] != 0.00010000 and utxo["spendable"]:
                balance += utxo["amount"]
        if balance > 100:
            logger.info(f"{balance} KMD in non-split UTXOs")
            logger.info(daemon.sendtoaddress(const.SWEEP_ADDR, round(balance-5, 4)))
        else:
            logger.info(f"Only {balance} KMD in non-split UTXOs, skipping sweep.")

    def restart(self, coin: str, docker=True) -> None:
        self.stop(coin, docker)
        self.start(coin, docker)

    def start(self, coin: str, docker=True) -> None:
        if not self.configured:
            return
        if docker:
             self.start_container(coin)
        if not docker:
            daemon = self.coins_data[coin]["daemon"]
            server = self.coins_data[coin]["server"]
            if server == "main":
                launch_params = self.coins_data[coin]["launch_params"]
                # check if already running
                try:
                    block_height = daemon.getblockcount()
                    if block_height:
                        logger.debug(f"{coin} daemon is already running.")
                        return
                except Exception as e:
                    logger.error(e)

                log_output = open(f"{self.log_path}/{coin}_daemon.log",'w+')
                subprocess.Popen(launch_params.split(" "), stdout=log_output, stderr=log_output, universal_newlines=True)
                time.sleep(3)
                logger.info('{:^60}'.format( f"{coin} daemon starting."))
                logger.info('{:^60}'.format( f"Use 'tail -f {coin}_daemon.log' for mm2 console messages."))
            # TODO: add non docker 3p server start
        self.wait_for_start(coin)

    def stop(self, coin: str, docker=True) -> None:
        if not self.configured:
            return
        # We shouldnt stop a chain until it is ready for RPCs
        self.wait_for_start(coin)
        if docker:
             self.stop_container(coin)
        if not docker:
            daemon = self.coins_data[coin]["daemon"]
            try:
                daemon.stop()
                self.wait_for_stop(coin)
            except Exception as e:
                logger.error(e)
            self.wait_for_stop(coin)
        
    def start_container(self, coin):
        server = self.coins_data[coin]["server"]
        if server == "main":
            compose = const.COMPOSE_PATH_MAIN
        else:
            compose = const.COMPOSE_PATH_3P
        try:
            subprocess.run(['docker', 'compose', '-f', compose, 'up', coin.lower(), '-d'], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(e)

    def stop_container(self, coin):
        server = self.coins_data[coin]["server"]
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
        daemon = self.coins_data[coin]["daemon"]
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
        daemon = self.coins_data[coin]["daemon"]
        i = 0
        while True:
            try:
                i += 1
                if i == 180:
                    logger.info(f"Looks like there might be an issue with loading {coin}...")
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
            time.sleep(5)
                


