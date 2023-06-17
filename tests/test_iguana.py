#!/usr/bin/env python3
from fixtures import setup_iguana
import const


def test_addnotary(setup_iguana):
    '''
    Tests to confirm Iguana is running and the Iguana class is working.
    '''
    iguana = setup_iguana
    for notary, ip_addr in const.NOTARY_PEERS.items():
        r = iguana.addnotary(ip_addr)
        # {"result":"notary node added","tag":"1048705532077274207"}
        assert r["result"] == "notary node added"