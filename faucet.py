#!/usr/bin/env python3
import requests
from color import ColorMsg



class Faucet():
    def __init__(self):
        self.drip_url = "https://notaryfaucet.dragonhound.tools/faucet"
        self.balance_url = "https://notaryfaucet.dragonhound.tools/faucet_balances"
        self.msg = ColorMsg()

    def balances(self, table=True):
        print(self.msg.colorize(f"\nGetting faucet balances...", "darkgrey"))
        r = requests.get(self.balance_url).json()
        if table:
            coins = list(r.keys())
            coins.sort()
            self.msg.status(f"\n{'='*25} Faucet Balances {'='*26}")
            for coin in coins:
                c = self.msg.colorize(f"{coin:>10}", "lightblue")
                b = self.msg.colorize(f"{r[coin]['balance']:>14}", "lightcyan")
                a = self.msg.colorize(f"{r[coin]['address']}", "lightcyan")
                x = self.msg.colorize(f"|", "lightblue")
                print(f"{x} {c} {x} {b} {x} {a} {x}")
            print(self.msg.colorize(f"{'-'*68}", "lightblue"))
        return r

    def drip(self, coin, pubkey):
        url = f"{self.drip_url}/{pubkey}/{coin}"
        return requests.get(url).json()
