#!/usr/bin/env python3
import time
from stats import Stats

nnstats = Stats()
while True:
    try:
        nnstats.show()
        print("Ctrl+C to exit to main menu.")
        time.sleep(600)
    except KeyboardInterrupt:
        break
