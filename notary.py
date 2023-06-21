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
    def __init__(self):
        self.config = Config().load()
        self.configured = self.check_config()
        self.addnotary = self.config["addnotary"]
        self.sweep_address = self.config["sweep_address"]
        self.coins_data = self.get_coins_data()
        self.log_path = f"{const.HOME}/logs"
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

    def check_config(self):
        if "addnotary" not in self.config:
            print("Node configuration missing. Select 'Configure' from the main menu to set your node config.")
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
                        "address": self.config[f"addresses_{server}"][coin],
                        "pubkey": self.config[f"pubkey_{server}"]
                    }
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
    
    def consolidate(self, coin: str) -> None:
        if not self.configured:
            return
        address = self.coins_data[coin]["address"]
        pubkey = self.coins_data[coin]["pubkey"]
        daemon = self.coins_data[coin]["daemon"]
        utxos_data = helper.get_utxos(coin, pubkey)
        if len(utxos_data) == 0:
            try:
                utxos_data = daemon.listunspent()
            except Exception as e:
                logger.error(f"Error getting UTXOs for {coin}: e")
                return

        utxos = sorted(utxos_data, key=lambda d: d['amount'], reverse=True) 
        if len(utxos) > 0:
            logger.info(f"Biggest {coin} UTXO: {utxos[0]['amount']}")
            logger.info(f"{len(utxos)} {coin} UTXOs")
        else:
            logger.debug(f"No UTXOs found for {coin}")

        inputs = []
        value = 0
        skipped_inputs = 0
        remaining_inputs = len(utxos)
        merge_amount = 800
        if len(utxos) < 20 and daemon.getbalance() > 0.001:
            logger.debug(f"< 20 UTXOs to consolidate {coin}, skipping")
            return

        logger.info(f"consolidating {coin}...")
        for utxo in utxos:
            # for daemon resp data
            if "satoshis" not in utxo:
                utxo["satoshis"] = utxo["amount"] * 100000000
            if utxo["confirmations"] < 100:
                skipped_inputs += 1
                remaining_inputs -= 1
                if remaining_inputs > 0:
                    continue
            else:
                remaining_inputs -= 1
            input_utxo = {"txid": utxo["txid"], "vout": utxo["vout"]}
            inputs.append(input_utxo)

            logger.debug(f"inputs: {len(inputs)}")
            logger.debug(f"value: {value}")
            logger.debug(f"remaining_inputs: {remaining_inputs}")
            value += utxo["satoshis"]
            if len(inputs) > merge_amount or remaining_inputs < 1:
                value = round(value/100000000, 8)
                if coin in ["EMC", "CHIPS", "AYA"]:
                    # Got -26 error if not reducing amount
                    vouts = {address: value - 0.001}
                else:
                    vouts = {address: value}
                try:
                    rawhex = daemon.createrawtransaction(inputs, vouts)
                    #logger.debug(f"rawhex: {rawhex}")
                    time.sleep(0.1)
                    if coin in ["AYA"]:
                        signedhex = daemon.signrawtransactionwithwallet(rawhex)
                    else:
                        signedhex = daemon.signrawtransaction(rawhex)
                    #logger.debug(f"signedhex: {signedhex}")
                    time.sleep(0.1)
                    txid = daemon.sendrawtransaction(signedhex["hex"])
                    logger.info(f"Sent {value} to {address}")
                    logger.info(f"txid: {txid}")
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(e)
                    #logger.debug(utxo)
                    #logger.debug(vouts)
                inputs = []
                value = 0
                if remaining_inputs < 0: remaining_inputs = 0
                logger.info(f"{remaining_inputs} remaining {coin} utxos to process")
                time.sleep(1)
        if skipped_inputs > 0:
            logger.debug(f"{skipped_inputs} {coin} UTXOs skipped due to < 100 confs")

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

    def stop(self, coin: str) -> None:
        if not self.configured:
            return
        daemon = self.coins_data[coin]["daemon"]
        try:
            daemon.stop()
            self.wait_for_stop(coin)
        except Exception as e:
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
                logger.debug(f"Waiting for {coin} daemon to stop...")
                time.sleep(15)
                block_height = daemon.get_blockheight(coin)
                if not block_height:
                    return True
            except Exception as e:
                logger.error(e)
                return True

    def wait_for_start(self, coin: str) -> bool:
        if not self.configured:
            return False
        daemon = self.coins_data[coin]["daemon"]
        launch_params = self.coins_data[coin]["launch_params"]
        i = 0
        while True:
            try:
                i += 1
                if i == 20:
                    logger.info(f"Looks like there might be an issue with loading {coin}...")
                    logger.info(f"We'll try and start it again, but if you need it here are the launch params to do it manually:")
                    logger.info(' '.join(launch_params))
                    # TODO: Send an alert if this happens
                    return False
                logger.debug(f"Waiting for {coin} daemon to restart...")
                time.sleep(30)
                block_height = daemon.get_blockheight(coin)
                if block_height:
                    return True
            except Exception as e:
                logger.error(e)
                pass

    def start(self, coin: str) -> None:
        if not self.configured:
            return
        daemon = self.coins_data[coin]["daemon"]
        server = self.coins_data[coin]["server"]
        if server == "main":
            launch_params = self.coins_data[coin]["launch_params"]
            # check if already running
            try:
                block_height = daemon.get_blockheight(coin)
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
        else:
            # TODO: Add support for starting 3p via docker
            pass
        self.wait_for_start(coin)
            


