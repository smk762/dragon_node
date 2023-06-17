
#!/usr/bin/env python3
import requests

class Iguana():
    def __init__(self, iguana_port):
        self.iguana_port = iguana_port

    def rpc(self, params):
        try:
            resp = requests.post(f"http://127.0.0.1:{self.iguana_port}", json=params).json()
            return resp
        except Exception as e:
            return {"txid": f"Error! Iguana down? {e}"}

    def split(self, coin, utxos=40, sats=10000):
        params={
            "agent": "iguana",
            "method": "splitfunds",
            "satoshis": f"{sats}",
            "sendflag": 1,
            "duplicates": utxos,
            "coin": coin
        }
        return self.rpc(params)
