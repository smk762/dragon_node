#!/usr/bin/env python3
from lib_atomicdex import *

msg = "Enter coin: "
coin = get_valid_coin(msg, DPOW_COINS)
msg = "Set utxo merge? [T/F]: "
valid_options = ["t", "f"]
q = get_valid_input(msg, valid_options)

activate_coins([coin], q == 't')