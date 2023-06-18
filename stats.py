#!/usr/bin/env python3
import time
import const
import helper
from daemon import DaemonRPC
from logger import logger

class StatsLine:
    def __init__(self, column_widths, coin="KMD"):
        # Todo: last mined KMD since
        self.coin = coin
        self.daemon = DaemonRPC(self.coin)
        self.col_widths = column_widths

    def last_block_time(self):
        best_block = self.daemon.rpc.getbestblockhash()
        best_blk_info = self.daemon.rpc.getblock(best_block)
        last_block = best_blk_info["time"]
        return last_block

    def ntx_utxo_count(self, utxo_value):
        utxo_value = helper.get_utxo_value(self.coin)
        unspent = self.daemon.get_unspent()
        count = 0
        for utxo in unspent:
            if utxo["amount"] == utxo_value:
                count += 1
        return count

    def connections(self):
        return "-"
        pass

    def wallet_size(self):
        return "-"
        pass

    def get(self):
        # Blocks
        block_count = self.daemon.getblockcount()
        last_block_time = self.daemon.block_time(block_count)
        since_last_block_time = int(time.time()) - last_block_time

        # Notarizations        
        wallet_tx = self.daemon.listtransactions()
        tx_count = len(wallet_tx)
        ntx_stats = helper.get_ntx_stats(wallet_tx, self.coin)
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
        return row


class Stats:
    def __init__(self, coins: list):
        self.coins = coins
        self.col_widths = [9, 6, 6, 6, 10, 12, 8, 6, 8, 8, 8]
        self.columns = [
            "COIN", "NTX", "LAST", "UTXO", "BALANCE",
            "BLOCKS", "LAST", "CONN", "SIZE", "NUMTX" "TIME"
        ]
        
    def format_line(self, row):
        line = "| "
        for i in range(len(row)):
            if i in [0]:
                line += f"{str(row[i]).ljust(self.col_widths[i])} |"
            else:
                line += f"{str(row[i]).rjust(self.col_widths[i])} |"
        return line
    
    def header(self):
        return self.format_line(self.columns)
    
    def spacer(self):
        return "-" * sum(self.col_widths)
    
    def show(self):
        print(self.header())
        print(self.spacer())
        for coin in self.coins:
            line = StatsLine(self.col_widths, coin)
            row = line.get()
            print(self.format_line(row))
