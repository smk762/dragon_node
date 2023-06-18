#!/usr/bin/env python3
import time
import const
import helper
from daemon import DaemonRPC
from logger import logger

class Stats:
    def __init__(self, coin="KMD"):
        self.col_widths = [9, 6, 6, 6, 10, 12, 8, 6, 8, 8, 8]
        self.columns = [
            "COIN", "NTX", "LAST", "UTXO", "BALANCE",
            "BLOCKS", "LAST", "CONN", "SIZE", "NUMTX" "TIME"
        ]
        self.coin = coin
        self.daemon = DaemonRPC(self.coin)

    def last_block_time(self):
        best_block = self.daemon.rpc.getbestblockhash()
        best_blk_info = self.daemon.rpc.getblock(best_block)
        last_block = best_blk_info["time"]
        return last_block

    def connections(self):
        return "-"
        pass

    def wallet_size(self):
        return "-"
        pass

    def stats_line(self):
        # Blocks
        block_count = self.daemon.getblockcount()
        last_block_time = self.daemon.block_time(block_count)
        since_last_block_time = int(time.time()) - last_block_time

        # Notarizations        
        wallet_tx = self.daemon.listtransactions()
        tx_count = len(wallet_tx)
        ntx_stats = self.get_ntx_stats(wallet_tx)
        ntx_count = ntx_stats[0]
        last_ntx_time = ntx_stats[1]
        last_mined = ntx_stats[2]

        # Wallet
        start = time.perf_counter()
        r = self.daemon.rpc("listunspent")
        response_time = time.perf_counter() - start
        response_time = f"{response_time:.4f}"

        ntx_utxo_count = self.ntx_utxo_count(self.coin)
        balance = self.daemon.getbalance()
        connections = self.connections()
        wallet_size = self.wallet_size()

        row = [
            self.coin, ntx_count, last_ntx_time, ntx_utxo_count,
            balance, block_count, since_last_block_time, connections,
            wallet_size, tx_count, response_time
        ]
        return self.format_line(row)

    def format_line(self, row):
        line = ""
        for i in range(len(row)):
            if i in [0]:
                line += f"{str(row[i]).ljust(self.col_widths[i])}"
            else:
                line += f"{str(row[i]).rjust(self.col_widths[i])}"
        return line
    
    def header(self):
        return self.format_line(self.columns)
    
    def spacer(self):
        return "-" * sum(self.col_widths)
    
    def get_ntx_stats(self, wallet_tx):
        last_ntx_time = 0
        last_mined_time = 0
        ntx = []
        ntx_addr = helper.get_ntx_address(self.coin)
        for tx in wallet_tx:            
            if "address" in tx:
                if tx["address"] == ntx_addr:

                    if tx["time"] > last_ntx_time:
                        last_ntx_time = tx["time"]

                    if tx["category"] == "send":
                        ntx.append(tx)

                if "generated" in tx:
                    if tx["time"] > last_mined_time:
                        last_mined_time = tx["time"]

        ntx_count = len(ntx)
        return [ntx_count, last_ntx_time, last_mined_time]
        
    def ntx_utxo_count(self, utxo_value):
        utxo_value = helper.get_utxo_value(self.coin)
        unspent = self.daemon.get_unspent()
        count = 0
        for utxo in unspent:
            logger.debug(utxo)
            if utxo["amount"] == utxo_value:
                count += 1
        return count
