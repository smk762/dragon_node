
import const
import helper
from color import ColorMsg
from configure import Config
from daemon import DaemonRPC
from notary import Notary
from logger import logger
import based_58


class TUI():
    def __init__(self):
        self.config = Config()
        self.msg = ColorMsg()
        self.servers = const.DPOW_SERVERS
    
    def list_addresses(self):
        nn = Notary()
        coins_ntx_data = nn.get_coins_ntx_data()
        coins = list(coins_ntx_data.keys())
        coins.sort()
        for coin in coins:
            self.msg.status(f"{coin:>16}: {coins_ntx_data[coin]['address']:<40}")
    
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
                addr_validation = daemon.validateaddress(address)
                logger.info(f"Validating {address}...")
                logger.info(f"Address: {addr_validation}")
                if "ismine" not in addr_validation:
                    logger.info(f"Importing {coin} private key...")
                    wif = helper.wif_convert(coin, wif)
                    r = daemon.importprivkey(wif)
                    logger.info(f"Address: {r}")
                elif not addr_validation["ismine"]:
                    logger.info(f"Importing {coin} private key...")
                    wif = helper.wif_convert(coin, wif)
                    r = daemon.importprivkey(wif)
                    logger.info(f"Address: {r}")
                else:
                    logger.info(f"Address {address} already imported.")
