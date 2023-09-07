#!/usr/bin/env python3
import time
import os
import const
import helper
import datetime
from daemon import DaemonRPC
from logger import logger
from color import ColorMsg
from notary import Notary
from iguana import Iguana
from pykomodefi import KomoDeFi_API


class StatsLine:
    def __init__(self, column_widths, coin="KMD", replenish_utxos=True):
        # Todo: last mined KMD since
        self.msg = ColorMsg()
        self.coin = coin
        self.daemon = DaemonRPC(self.coin)
        self.notary = Notary()
        self.col_widths = column_widths
        self.replenish_utxos = replenish_utxos
    
    # To check if daemon pubkey matches config
    def test_pubkey(self):
        pass
            
    def last_block_time(self):
        best_block = self.daemon.rpc.getbestblockhash()
        best_blk_info = self.daemon.rpc.getblock(best_block)
        last_block = best_blk_info["time"]
        return last_block

    def ntx_utxo_count(self):
        utxo_value = helper.get_utxo_value(self.coin)
        return self.daemon.get_utxo_count(utxo_value)

    def connections(self):
        networkinfo = self.daemon.getnetworkinfo()
        return networkinfo["connections"]

    def wallet_size(self):
        filename = helper.get_wallet_path(self.coin)
        filesize = os.path.getsize(filename)
        if filesize > 10485760:
            return '\033[31m' + " > 10M" + '\033[0m' 
        elif filesize > 3145728:
            return '\033[33m' + f"  > 3M" + '\033[0m' 
        elif filesize < 1048576:
            return '\033[92m' + f"  < 1M" + '\033[0m' 
        else:
            return helper.bytes_to_unit(filesize)

    def get(self) -> list:
        if self.coin == "KMD_3P":
            row = ["KMD (3P)"]
        elif self.coin in const.COINS_3P:
            row = [f"{self.coin} (3P)"]
        else:
            row = [self.coin]
        try:
            # Balance
            balance = self.daemon.getbalance()
            if balance < 0.1:
                balance = '\033[31m' + f"     {balance:.3f}" + '\033[0m'
            else:
                balance = f"{balance:.3f}"
            row.append(balance)
            
            # UTXOS
            ntx_utxo_count = self.ntx_utxo_count()
            if ntx_utxo_count < 5:
                ntx_utxo_count = '\033[31m' + f"     {ntx_utxo_count}" + '\033[0m'
            elif ntx_utxo_count < 10:
                ntx_utxo_count = '\033[33m' + f"     {ntx_utxo_count}" + '\033[0m'
            elif ntx_utxo_count > 100:
                ntx_utxo_count = '\033[31m' + " > 100" + '\033[0m'
            elif ntx_utxo_count > 40:
                ntx_utxo_count = '\033[92m' + f"    {ntx_utxo_count}" + '\033[0m'
            elif ntx_utxo_count >= 10:
                ntx_utxo_count = '\033[92m' + f"    {ntx_utxo_count}" + '\033[0m'
            row.append(str(ntx_utxo_count))

            # Notarizations        
            wallet_tx = self.daemon.listtransactions()
            ntx_stats = helper.get_ntx_stats(wallet_tx, self.coin)
            ntx_count = ntx_stats[0]
            row.append(str(ntx_count))
            
            # Since NTX
            last_ntx_time = ntx_stats[1]
            if last_ntx_time == 0:
                dhms_since_ntx = '\033[31m' + "   Never" + '\033[0m'
            else:
                sec_since = helper.sec_since(last_ntx_time)
                dhms_since_ntx = helper.sec_to_dhms(sec_since)
            row.append(dhms_since_ntx)
            
            # Blocks
            block_count = self.daemon.getblockcount()
            row.append(str(block_count))
            last_blocktime = self.daemon.last_block_time(block_count)
            if last_blocktime == 0:
                dhms_since_block = '\033[31m' + "  Never " + '\033[0m' 
            else:
                sec_since = helper.sec_since(last_blocktime)
                dhms_since_block = helper.sec_to_dhms(sec_since, True, 600, 1800, 7200)
            row.append(dhms_since_block)

            # Connections
            connections = self.connections()
            row.append(str(connections))
            
            # Wallet size
            wallet_size = self.wallet_size()
            row.append(str(wallet_size))
            
            # TX Count
            tx_count = len(wallet_tx)
            row.append(str(tx_count))
            
            # Response time
            start = time.perf_counter()
            r = self.daemon.rpc("listunspent")
            response_time = time.perf_counter() - start
            row.append(f"{response_time:.4f}")
                
            if self.coin == "KMD":
                # Last Mined
                last_mined_ts = ntx_stats[2]
                last_mined_sec = helper.sec_since(last_mined_ts)
                last_mined = helper.sec_to_dhms(last_mined_sec, padding=False, color=False)
                if last_mined_sec > 14400:
                    last_mined = '\033[35m' + last_mined + '\033[0m'
                else:
                    last_mined = '\033[92m' + last_mined + '\033[0m'
                row.append(last_mined)
        except Exception as e:
            # print(e)
            while len(row) < 11:
                row.append("-")
        return row


class Stats:
    def __init__(self, coins: list=const.DPOW_COINS) -> None:
        self.coins = coins
        self.coins.sort()
        self.msg = ColorMsg()
        self.col_widths = [11, 10, 6, 6,
                           8, 8, 8, 6,
                           6, 8, 8]
        self.columns = [
            "COIN", "BALANCE", "UTXO", "NTX",
            "LASTNTX", "BLOCKS", "LASTBLK", "CONN",
            "SIZE", "NUMTX", "TIME"
        ]
        self.table_width = sum(self.col_widths) + 2 * (len(self.col_widths)) + 3
        
    def format_line(self, row: list, color: str="") -> str:
        line = " | "
        for i in range(len(row)):
            if i in [0]:
                line += f"{str(row[i]).ljust(self.col_widths[i])} |"
            else:
                line += f"{str(row[i]).rjust(self.col_widths[i])} |"
        if color != "":
            return self.msg.colorize(line, color)
        else:
            return line

    def datetime_str(self) -> str:
        date_str = self.msg.colorize(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', "darkgrey")
        date_str = f"{date_str:>119}"
        return date_str
    
    def header(self) -> str:
        return self.format_line(self.columns)
    
    def footer(self, mined_str) -> str:
        daemon = DaemonRPC("KMD")
        iguana_main = Iguana('main')
        iguana_3p = Iguana('3p')
        try:
            dex = KomoDeFi_API(const.MM2_JSON_PATH)
            dex_version = dex.version.split("_")[-1]
            if dex_version != "Error":
                active_versions = helper.get_active_seednode_versions()
                if dex_version in active_versions:
                    dex_status = self.msg.colorize(f"[ DeFi API \N{check mark} {dex_version} ]", "lightgreen")
                else:
                    dex_status = self.msg.colorize(f"[ DeFi API \N{runic cross punctuation} {dex_version} ]", "purple")
            else:
                dex_status = self.msg.colorize(f"[ DeFi API \N{runic cross punctuation} {dex_version} ]", "darkgrey")
        except FileNotFoundError:
            dex_status = self.msg.colorize(f"[ DeFi API \N{runic cross punctuation} Err:404 ]", "darkgrey")
        
        if daemon.is_mining():
            mining = self.msg.colorize(f"[ Mining \N{check mark} {mined_str}]", "lightgreen")
        else:
            mining = self.msg.colorize(f"[ Mining \N{runic cross punctuation} ]", "darkgrey")
        if iguana_main.test_connection():
            status_main = self.msg.colorize(f"[ dPoW Main \N{check mark} ]", "lightgreen")
        else:
            status_main = self.msg.colorize(f"[ dPoW Main \N{runic cross punctuation} ]", "darkgrey")
        if iguana_3p.test_connection():
            status_3p = self.msg.colorize(f"[ dPoW 3P \N{check mark} ]", "lightgreen")
        else:
            status_3p = self.msg.colorize(f"[ dPoW 3P \N{runic cross punctuation} ]", "darkgrey")

        status_data = f" \N{position indicator} ".join([status_main, status_3p, mining, dex_status]) 
        footer_row = f"\N{position indicator} {status_data} \N{position indicator}"
        return footer_row.center(155)
    
    def spacer(self) -> str:
        return " " + "-" * (self.table_width - 1)

    def show(self, replenish_utxos=True) -> None:
        print()
        print(self.datetime_str())
        print(self.header())
        print(self.spacer())
        mined_str = ""
        for coin in self.coins:
            line = StatsLine(self.col_widths, coin, replenish_utxos)
            row = line.get()
            if coin == "KMD":
                mined_str = f"{row.pop(-1)}"
            if row[-1] == "-":
                print(self.format_line(row, "darkgrey"))
            else:
                print(self.format_line(row))
        print(self.spacer())
        print(self.footer(mined_str))
       