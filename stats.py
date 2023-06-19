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

    def get(self) -> list:
        if self.coin == "KMD_3P":
            row = ["KMD (3P)"]
        elif self.coin in const.COINS_3P:
            row = [f"{self.coin} (3P)"]
        else:
            row = [self.coin]
        try:
            # Notarizations        
            wallet_tx = self.daemon.listtransactions()
            ntx_stats = helper.get_ntx_stats(wallet_tx, self.coin)
            ntx_count = ntx_stats[0]
            row.append(str(ntx_count))
            
            last_ntx_time = ntx_stats[1]
            row.append(str(last_ntx_time))
            last_mined = ntx_stats[2]

            ntx_utxo_count = self.ntx_utxo_count(self.coin)
            row.append(str(ntx_utxo_count))

            balance = self.daemon.getbalance()
            row.append(f"{balance:.4f}")

            # Blocks
            block_count = self.daemon.getblockcount()
            row.append(str(block_count))
            since_last_block_time = self.daemon.time_since_block(block_count)
            row.append(str(since_last_block_time))

            connections = self.connections()
            row.append(str(connections))
            
            wallet_size = self.wallet_size()
            row.append(str(wallet_size))
            
            tx_count = len(wallet_tx)
            row.append(str(tx_count))
            
            start = time.perf_counter()
            r = self.daemon.rpc("listunspent")
            response_time = time.perf_counter() - start
            row.append(f"{response_time:.4f}")

        except Exception as e:
            logger.error(f"Error getting stats for {self.coin}: {e}")
        return row


class Stats:
    def __init__(self, coins: list):
        self.coins = coins
        self.col_widths = [12, 6, 8, 6, 10, 10, 8, 6, 8, 8, 8]
        self.columns = [
            "COIN", "NTX", "LASTNTX", "UTXO", "BALANCE",
            "BLOCKS", "LASTBLK", "CONN", "SIZE", "NUMTX", "TIME"
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
        return "-" * (sum(self.col_widths) + 2 * (len(self.col_widths) + 1))
    
    def show(self):
        print()
        print(self.header())
        print(self.spacer())
        for coin in self.coins:
            line = StatsLine(self.col_widths, coin)
            row = line.get()
            print(self.format_line(row))
        print()
