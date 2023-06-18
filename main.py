from color import ColorMsg
import helper
import const
import tui
from configure import Config
from stats import Stats
from tui import TUI

color_msg = ColorMsg()
config = Config()
stats = Stats()
tui = TUI()

print('''
  ________                                         _____   __     _________      
  ___  __ `____________ _ _____ _____________      ___/ | / /___________/ /____  
  __  / / /_/ ___// __ `/ / __ ` / __ `_/ __ `     __/  |/ / / __ `/ __  / / _ ` 
  _  /_/ /_/ /   / /_/ / / /_/ // /_/ // / / /     _/ /|  / / /_/ / /_/ / /  __/ 
  /_____/ /_/    `__,_/  `__, / `____//_/ /_/      /_/ |_/  `____/`__,_/  `___/  
                        /____/                                                   
''' + '{:^80}'.format('Dragon Node TUI v0.2 by Dragonhound'))

options = ["configure", "stats", "convert_privkey", "import_privkey"]
while True:
    color_msg.status(f"\n==== Options ====")
    for i in range(len(options)):
        color_msg.option(f'[{i}] {options[i].title().replace("_", " ")}')
    color_msg.option(f"[{len(options)}] Exit")
    q = color_msg.input("Select an option:")
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
            
        elif options[q] == "convert_privkey":
            wif = input("Enter private key: ")
            for coin in const.DPOW_COINS:
                if coin != "KMD_3P":
                    print(f"{coin}: {helper.wif_convert(coin, wif)}")
        
        elif options[q] == "stats":
            # Todo: last mined KMD since
            print(stats.header())
            print(stats.spacer())
            for coin in const.DPOW_COINS:
                print(stats.stats_line())
        
        elif options[q] == "import_privkey":
            tui.import_privkey()
            break
                
        elif options[q] == "exit":
            break