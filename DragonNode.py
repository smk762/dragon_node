#!/usr/bin/env python3
from lib_atomicdex import *
import lib_tui


header = "\
  ________                                         _____   __     _________      \n\
  ___  __ \____________ _ _____ _____________      ___/ | / /___________/ /____  \n\
  __  / / /_/ ___// __ `/_/ __ ` / __ \_/ __ \     __/  |/ /_/ __ \/ __  /_/ _ \ \n\
  _  /_/ /_/ /   / /_/ /_/ /_/ // /_/ // / / /     _/ /|  / / /_/ / /_/ / /  __/ \n\
  /_____/ /_/    \__,_/ _\__, / \____//_/ /_/      /_/ |_/  \____/\__,_/  \___/  \n\
                        /____/                                                   \n"

author = '{:^80}'.format('Welcome to the Dragon Node TUI v0.1 by Dragonhound')

def main():

    menu_items = [
        {"View Balances": lib_tui.view_balances},
        {"View Stats": lib_tui.view_stats},
        {"Show Launch Params": lib_tui.show_launch_params},
        {"Refresh Wallet": lib_tui.refresh_wallet},
        {"Loop Views": lib_tui.loop_views},
        {"Merge UTXOs": lib_tui.merge_utxos},
        {"Withdraw Funds": lib_tui.withdraw_funds},
        {"Exit TUI": lib_tui.exit_tui}
    ]

    while True:
        try:
            os.system('clear')
            print(colorize(header, 'lightgreen'))
            print(colorize(author, 'cyan'))
            get_status()
            print("")

            try:
                for item in menu_items:
                    print(colorize(" [" + str(menu_items.index(item)) + "] ", 'blue') + colorize(list(item.keys())[0],'blue'))
                choice = color_input(" Select menu option: ")
                if int(choice) < 0:
                    raise ValueError
                print("")
                list(menu_items[int(choice)].values())[0]()
                print("")
                wait_continue()
            except (ValueError, IndexError):
                pass

        except KeyboardInterrupt:
            lib_tui.exit_tui()


if __name__ == "__main__":

    while True:
        os.system('clear')
        print("\n")

        with (open("logo.txt", "r")) as logo:

            for line in logo:
                parts = line.split(' ')
                row = ''
                for part in parts:
                    if part.find('~') == -1:
                        row += colorize(part, 'blue')
                    else:
                        row += colorize(part, 'black')
                print(row, end='')
                #print(line, end='')
                time.sleep(0.04)
            time.sleep(0.4)

        print("\n")
        break
    activate_coins(DPOW_COINS)
    main()