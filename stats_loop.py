#!/usr/bin/env python3
import time
from stats import Stats
from color import ColorMsg
from iguana import Iguana

nnstats = Stats()
msg = ColorMsg()
    
while True:
    try:
        nnstats.show()
        iguana = Iguana("main")
        err = []
        if not iguana.test_connection():
            err.append("[Main Iguana down!]")
        iguana = Iguana("3p")
        if not iguana.test_connection():
            err.append("[3P Iguana down!]")
        if len(err) > 0:
            msg.error(" " + '   '.join(err))
        print()
        msg.status(" Ctrl+C to exit to main menu.")
        time.sleep(600)
    except KeyboardInterrupt:
        break
