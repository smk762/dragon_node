#!/usr/bin/env python3
import const
import helper
from daemon import DaemonRPC

class Stats:
    def __init__(self, coin="KMD"):
        self.col_widths = [9, 6, 6, 6, 10, 12, 8, 6, 8, 8, 8]
        self.columns = [
            "COIN", "NTX", "LAST", "UTXO", "BALANCE",
            "BLOCKS", "LAST", "CONN", "SIZE", "NUMTX" "TIME"
        ]
        self.coin = coin
        self.daemon = DaemonRPC(self.coin)

    def ntx_utxo_count(self, coin):
        return self.get_split_utxo_count(coin)

    def balance(self, coin):
        return self.daemon.rpc("balance")

    def block_count(self, coin):
        self.daemon.rpc("getblockcount")

    def last_block_time(self, coin):
        best_block = self.daemon.rpc.getbestblockhash()
        best_blk_info = self.daemon.rpc.getblock(best_block)
        last_block = best_blk_info["time"]
        return last_block

    def connections(self, coin):
        return "-"
        pass

    def wallet_size(self, coin):
        return "-"
        pass

    def response_time(self, coin):
        return self.daemon.rpc_response_time("listunspent")

    def stats_line(self, coin):
        wallet_tx = self.daemon.listtransactions()
        tx_count = len(wallet_tx)
        ntx_stats = self.get_ntx_stats(wallet_tx)
        ntx_count = ntx_stats[0]
        last_ntx_time = ntx_stats[1]
        last_mined = ntx_stats[2]
        ntx_utxo_count = self.ntx_utxo_count(coin)
        balance = self.balance(coin)
        block_count = self.block_count(coin)
        last_block_time = self.last_block_time(coin)
        connections = self.connections(coin)
        wallet_size = self.wallet_size(coin)
        response_time = self.response_time(coin)
        
        row = [
            coin, ntx_count, last_ntx_time, ntx_utxo_count,
            balance, block_count, last_block_time, connections,
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
        
    def get_split_utxo_count(self, utxo_value=0.00010000):
        daemon = DaemonRPC(self.coin)
        if self.coin in const.LARGE_UTXO_COINS:
            utxo_value = 0.00100000
        unspent = daemon.get_unspent()
        count = 0
        for utxo in unspent:
            print(utxo)
            #if utxo["amount"] == utxo_value:
            #    count += 1
        return count