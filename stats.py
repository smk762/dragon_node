#!/usr/bin/env python3
import time
import const
import helper
import datetime
from daemon import DaemonRPC
from logger import logger
from color import ColorMsg

class StatsLine:
    def __init__(self, column_widths, coin="KMD"):
        # Todo: last mined KMD since
        self.coin = coin
        self.daemon = DaemonRPC(self.coin)
        self.col_widths = column_widths
        self.msg = ColorMsg()

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
            if last_ntx_time == 0:
                dhms_since = '\033[31m' + "  Never" + '\033[0m' 
            else:
                sec_since = helper.sec_since(last_ntx_time)
                dhms_since = helper.sec_to_dhms(sec_since, 3600)
            row.append(dhms_since)
            
            last_mined = ntx_stats[2]

            ntx_utxo_count = self.ntx_utxo_count(self.coin)
            row.append(str(ntx_utxo_count))

            balance = self.daemon.getbalance()
            if balance < 0.1:
                row.append('\033[31m' + f"     {balance:.3f}" + '\033[0m')
            else:
                row.append(f"{balance:.3f}")

            # Blocks
            block_count = self.daemon.getblockcount()
            row.append(str(block_count))
            last_blocktime = self.daemon.last_block_time(block_count)
            if last_blocktime == 0:
                dhms_since = '\033[31m' + "  Never" + '\033[0m' 
            else:
                sec_since = helper.sec_since(last_blocktime)
                dhms_since = helper.sec_to_dhms(sec_since, 3600)
            row.append(str(dhms_since))

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
            self.msg.warning(f"Error getting stats for {self.coin}: {e}")
        return row


class Stats:
    def __init__(self, coins: list):
        self.coins = coins
        self.coins.sort()
        self.col_widths = [12, 6, 8, 6, 10, 10, 8, 6, 8, 8, 8]
        self.columns = [
            "COIN", "NTX", "LASTNTX", "UTXO", "BALANCE",
            "BLOCKS", "LASTBLK", "CONN", "SIZE", "NUMTX", "TIME"
        ]
        self.table_width = sum(self.col_widths) + 2 * (len(self.col_widths) + 1)
        
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
        return "-" * self.table_width
    
    def show(self):
        print()
        print(self.header())
        print(self.spacer())
        for coin in self.coins:
            line = StatsLine(self.col_widths, coin)
            if line.daemon.rpcport != 0:
                row = line.get()
                print(self.format_line(row))
        print(self.spacer())
        date_str = '| ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ' |'
        fmt_date_str = str(date_str).rjust(self.table_width)
        print(fmt_date_str)
