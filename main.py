import datetime
import time
from color import ColorMsg
import helper
import const
import tui
from daemon import DaemonRPC
from configure import Config
from stats import Stats
from tui import TUI
from notary import Notary

color_msg = ColorMsg()
config = Config()
stats = Stats(const.DPOW_COINS)
tui = TUI()

print('''
  ________                                         _____   __     _________      
  ___  __ `____________ _ _____ _____________      ___/ | / /___________/ /____  
  __  / / /_/ ___// __ `/ / __ ` / __ `_/ __ `     __/  |/ / / __ `/ __  / / _ ` 
  _  /_/ /_/ /   / /_/ / / /_/ // /_/ // / / /     _/ /|  / / /_/ / /_/ / /  __/ 
  /_____/ /_/    `__,_/  `__, / `____//_/ /_/      /_/ |_/  `____/`__,_/  `___/  
                        /____/                                                   
''' + '{:^80}'.format('Dragon Node TUI v0.2 by Dragonhound'))
print()
notary = Notary()
if notary.configured:
    notary.welcome()


options = ["configure", "consolidate", "stats", "convert_privkey",
           "import_privkey", "reset_wallet", "start_coin", "stop_coin",
           "restart_coin", "list_addresses"]
while True:
    color_msg.status(f"\n  ==== Main Menu ====")
    for i in range(len(options)):
        color_msg.option(f'  [{i}] {options[i].title().replace("_", " ")}')
    color_msg.option(f"  [{len(options)}] Exit")
    q = color_msg.input("Select an option: ")
    try:
        q = int(q)
    except ValueError:
        color_msg.error("Invalid option, try again.")
        continue
    if q == len(options):
        break
    elif q > len(options):
        color_msg.error("Invalid option, try again.")
    else:

        if options[q] == "configure":
            config.create()
        if options[q] == "consolidate":
            notary = Notary()
            if notary.configured:
                coin = input("Enter coin to consolidate (or ALL): ")
                q = input("Force consolidation? (y/n): ")
                if q.lower() == "y":
                    force = True
                else:
                    force = False                    
                if coin.lower() == "all":
                    for coin in const.DPOW_COINS:
                        notary.consolidate(coin, force, force)
                elif coin.upper() in const.DPOW_COINS:
                    notary.consolidate(coin, force, force)
                else:
                    color_msg.error(f"Invalid coin '{coin}', try again.")
            else:
                color_msg.error(f"Node configuration missing. Select 'Configure' from the main menu to set your node config.")

        elif options[q] == "convert_privkey":
            wif = input("Enter private key: ")
            for coin in const.DPOW_COINS:
                if coin != "KMD_3P":
                    print(f"{coin}: {helper.wif_convert(coin, wif)}")

        elif options[q] == "reset_wallet":
            notary = Notary()
            if notary.configured:
                coin = input("Enter coin to reset wallet (or ALL): ")
                if coin.lower() == "all":
                    for coin in const.DPOW_COINS:
                        notary.reset_wallet(coin)                        
                elif coin.upper() in const.DPOW_COINS:
                    notary.reset_wallet(coin)                    
                else:
                    color_msg.error(f"Invalid coin '{coin}', try again.")

        elif options[q] == "stats":
            while True:
                try:
                    stats.show()
                    print("Ctrl+C to exit to main menu.")
                    time.sleep(600)
                except KeyboardInterrupt:
                    break

        elif options[q] == "import_privkey":
            tui.import_privkey()

        elif options[q] == "list_addresses":
            tui.list_addresses()

        elif options[q] == "start_coin":
            notary = Notary()
            coin = input("Enter coin to start (or ALL): ")
            if coin.lower() == "all":
                for coin in const.DPOW_COINS:
                    notary.start(coin)
            elif coin.upper() in const.DPOW_COINS:
                notary.start(coin)
            else:
                color_msg.error(f"Invalid coin '{coin}', try again.")

        elif options[q] == "restart_coin":
            notary = Notary()
            coin = input("Enter coin to restart (or ALL): ")
            if coin.lower() == "all":
                for coin in const.DPOW_COINS:
                    notary.restart(coin)
            elif coin.upper() in const.DPOW_COINS:
                notary.restart(coin)
            else:
                color_msg.error(f"Invalid coin '{coin}', try again.")

        elif options[q] == "stop_coin":
            notary = Notary()
            coin = input("Enter coin to stop (or ALL): ")
            if coin.lower() == "all":
                for coin in const.DPOW_COINS:
                    notary.stop(coin)
            elif coin.upper() in const.DPOW_COINS:
                notary.stop(coin)
            else:
                color_msg.error(f"Invalid coin '{coin}', try again.")

        elif options[q] == "exit":
            break
