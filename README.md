# Dragon Node

A node management tool for Komodo Platform Notary Node Operations

---
## Requirements

`pip3 install -r requirements.txt`

---
## Setup

1. Clone this repository: `git clone https://github.com/smk762/dragon_node`
2. Run `./setup` to install dependencies and initialize the dPoW submodule.
3. Use `./run` to launch the TUI
4. Use `./stats` to enter a stats display loop
5. Use `./update` to update the repo and dPoW submodule. It will default to the dPoW master branch, but you can override it with `./update BRANCH` to use a different branch.

---
## Features
- [x] Private key conversion
- [x] Address list from pubkey
- [x] dPoW stats display loop
- [x] KMD funds splitting (runs automatically when running `./stats`)
- [x] Funds conolidation
- [x] Wallet reset (work in progress)
- [x] Start/stop/update coins
- [ ] Start/stop/update dPoW
- [ ] KMD funds sweeping
- [ ] Add whitelist addresses to conf files
- [ ] Add peer IPs for addnode to conf files