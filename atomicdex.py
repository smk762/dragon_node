#!/usr/bin/env python3
import os
import json
import requests
from logger import logger
import const

class AtomicDEX():
    def __init__(self, config=const.MM2_JSON_PATH):
        if os.path.isfile(const.MM2_JSON_PATH):
            with open(const.MM2_JSON_PATH, "r") as f:
                conf = json.load(f)
            self.userpass = conf["rpc_password"]
        else:
            logger.info(f"MM2 config not found at {const.MM2_JSON_PATH}!")
            logger.info("To set it up, you should run `./setup_mm2` from the the notary_docker_3p repository:")
            self.userpass = "userpass"
        self.mm2_ip = f'http://127.0.0.1:7783'
           
    def rpc(self, method, params=None):
        if not params:
            params = {}
        params.update({
            "method": method,
            "userpass": self.userpass
        })
        r = requests.post(self.mm2_ip, json.dumps(params))
        return r

    def version(self):
        try:
            return self.rpc("version").json()["result"]
        except:
            return "Error"
    