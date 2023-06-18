
import const
import helper
from configure import Config
from daemon import DaemonRPC
from logger import logger
import based_58


class TUI():
    def __init__(self):
        self.config = Config()
        self.servers = const.DPOW_SERVERS
    
    def import_privkey(self):
        config = self.config.load()
        server = input(f"Select server {self.servers}: ")
        wif = input("Enter private key: ")
        # Does it match the pubkey for this server?
        pubkey = config[f"pubkey_{server}"]
        if not helper.validate_wif(pubkey, wif):
            logger.error("Private key does not match public key for this server!")
        else:
            for coin in const.CONF_PATHS[server]:
                # Check to see if already imported
                address = based_58.get_addr_from_pubkey(pubkey, coin)
                daemon = DaemonRPC(coin)
                addr_validation = daemon.validateaddress(address)["result"]
                if not addr_validation["ismine"]:
                    logger.info(f"Importing {coin} private key...")
                    wif = helper.wif_convert(coin, wif)
                    r = daemon.importprivkey(wif)
                    logger.info(f"Address: {r}")
                else:
                    logger.info(f"Address {address} already imported.")
