#!/usr/bin/env python3
import sys
from color import ColorMsg
from tui import TUI
from notary import Notary

color_msg = ColorMsg()
tui = TUI()
notary = Notary()

print('''
  ________                                         _____   __     _________      
  ___  __ `____________ _ _____ _____________      ___/ | / /___________/ /____  
  __  / / /_/ ___// __ `/ / __ ` / __ `_/ __ `     __/  |/ / / __ `/ __  / / _ ` 
  _  /_/ /_/ /   / /_/ / / /_/ // /_/ // / / /     _/ /|  / / /_/ / /_/ / /  __/ 
  /_____/ /_/    `__,_/  `__, / `____//_/ /_/      /_/ |_/  `____/`__,_/  `___/  
                        /____/                                                   
''' + '{:^80}'.format('Dragon Node TUI v0.2 by Dragonhound'))
print()
if notary.configured:
    notary.welcome()


menu = [
    {"configure": tui.configure},
    {"consolidate": tui.consolidate},
    {"convert_privkey": tui.convert_privkey},
    {"reset_wallet": tui.reset_wallet},
    {"stats": tui.stats},
    {"import_privkey": tui.import_privkey},
    {"list_addresses": tui.list_addresses},
    {"start_coin": tui.start_coin},
    {"restart_coin": tui.restart_coin},
    {"stop_coin": tui.stop_coin},
    {"exit": tui.exit}
]

while True:
    try:
        color_msg.status(f"\n  ==== Main Menu ====")
        for i in range(len(menu)):
            for k, v in menu[i].items():
                color_msg.option(f'  [{i}] {k.title().replace("_", " ")}')
        q = color_msg.input("Select an option: ")
        try:
            q = int(q)
        except ValueError:
            color_msg.error("Invalid option, try again.")
            continue
        if q > len(menu):
            color_msg.error("Invalid option, try again.")
        else:
            for k, v in menu[q].items():
                v()
    except KeyboardInterrupt:
        sys.exit(0)
