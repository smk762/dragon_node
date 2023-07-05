# Dragon Node

A node management tool for Komodo Platform Notary Node Operations

---
## Setup
1. Clone this repository: `git clone https://github.com/smk762/dragon_node`. Use the `season-seven` branch, or `season-sever-dev` if you want to test the latest features.
2. Run `./setup` to install dependencies

---
## Usage

3. Use `./tui` to launch the TUI
4. Use `./stats` to enter a stats display loop
5. Use `./split` to split utxos (can be run in crontab)
6. Use `./start_main` or `./start_3p`, to launch iguana for a server, or run `./start_dpow`, to launch iguana for both servers

---
## Features
- [x] Private key conversion
- [x] Private key import (for each server)
- [x] Private key list (from KMD pk)
- [x] Address list from pubkey
- [x] dPoW stats display loop
- [x] UTXO splitting (in tui, or can run in crontab via `./split`)
- [x] Funds conolidation
- [ ] Wallet reset (work in progress - use at own risk; some 3P coins not supported)
- [ ] Automated KMD funds sweeping
- [ ] Automated Mining activation/deactivation
- [ ] Add whitelist addresses to conf files
- [ ] Add peer IPs for addnode to conf files

---
## Configuration

To use the `consolidate` feature for EMC2 and MIL, you will need an API key from https://chainz.cryptoid.info/api.dws
This API key should be stored in a `.env` file in the root directory of the project. For example:

```bash
CRYPTOID_API_KEY=xxNotARealKeyxx
```

User config can be edited via the TUI, or by manually editing the `config.json` file. For example:

```json
{
    "userhome": "/home/dragonhound",
    "sweep_address": "RQBvgJ3D6HesSfJ1ZdQwAn9XfdXGWsxTSL",
    "pubkey_main": "039bb16266b0216264e7d3ccae12633105e1c14bd5d0e144e8b9c2b6d298a6c545",
    "pubkey_3p": "026d378de09ba51d8f56be52bc8d02f5e20bae843406e23686047b76c72412a7b3",
    "addnode": {
        "komodostats": "seed.komodostats.com",
        "webworker": "seed.webworker.sh"
    },
    "whitelist": {
        "s6_dragonhound_DEV_main": "RDragoNHdwovvsDLSLMiAEzEArAD3kq6FN",
        "s6_dragonhound_DEV_3p": "RLdmqsXEor84FC8wqDAZbkmJLpgf2nUSkq",
        "s7_dragonhound_DEV_main": "RHi882Amab35uXjqBZjVxgEgmkkMu454KK",
        "s7_dragonhound_DEV_3p": "RHound8PpyhVLfi56dC7MK3ZvvkAmB3bvQ"
    },
    "addnotary": {
        "dragonhound_AR": "15.235.204.174",
        "dragonhound_NA": "209.222.101.247",
        "dragonhound_DEV": "103.195.100.32"
    },
    "addresses": {
        "KMD_3P": "RCNyZmHjqPrru1SiijA4fgUeEKZ6u2JVvD",
        "VRSC": "RCNyZmHjqPrru1SiijA4fgUeEKZ6u2JVvD",
        "TOKEL": "RCNyZmHjqPrru1SiijA4fgUeEKZ6u2JVvD",
        "MCL": "RCNyZmHjqPrru1SiijA4fgUeEKZ6u2JVvD",
        "AYA": "AJsf8kG5ZiiSdyHWpCqGj3QXwf2CdsPmDu",
        "EMC2": "ELFgyqExfXMCpJgP4QATaJ8QEhbdj5wGyy",
        "MIL": "MAzwigJrjbE6ig3rUXpspRkmwGyfkrEjZF",
        "CHIPS": "RCNyZmHjqPrru1SiijA4fgUeEKZ6u2JVvD",
        "PIRATE": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "CCL": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "CLC": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "ILN": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "SUPERNET": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "DOC": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "MARTY": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "LTC": "Lga1bKF6FSHx9RqbC4gE1iS4PFncyaQ7W9",
        "GLEEC": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "KOIN": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "THC": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "KMD": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE",
        "NINJA": "RWdFQcpYmbrTxdWdV6g3qDhVwJswVQCGWE"
    },
    "split amount": "22",
    "split_threshold": "15"
}
```

Note: Addresses (except for the sweep address) are automatically calculated from pubkeys, so these are considered `readonly` in the app. If you want to change an address, you should change the pubkey.
