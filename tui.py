
import const
import helper
from configure import Config
from daemon import DaemonRPC
from logger import logger


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
                logger.info(f"Importing {coin} private key...")
                wif = helper.wif_convert(coin, wif)
                daemon = DaemonRPC(coin)
                r = daemon.importprivkey(wif)
                logger.info(f"Address: {r}")

        
    
    
    