import os
import sqlite3
import sys
import unittest
from BaseTestCase import BaseTestCase

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)
import networks
import tables


class TestNetworks(BaseTestCase, unittest.TestCase):

    def testAddAll(self):
        networks.add_all(self.c)
        nbr_of_networks = self._query('SELECT COUNT(*) as nbr_of_networks FROM network')[0][0]
        self.assertEquals(
            nbr_of_networks,
            4,
            "Additional or missing networks")

    def testAddAllRFC1918(self):
        networks.add_all_rfc_1918(self.c)
        expected_networks = ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']
        expected_netmasks = ['255.0.0.0', '255.240.0.0', '255.255.0.0']
        actual_networks = self._query('SELECT * FROM network')
        self.assertEquals(
            len(actual_networks),
            len(expected_networks),
            "Additional or missing networks")

        for network in actual_networks:
            self.assertTrue(
                network.ipv4_txt in expected_networks,
                "Network not amongst expected network")
            self.assertEquals(
                network.ipv4_netmask_txt,
                expected_netmasks[expected_networks.index(network[6])],
                "Wrong netmask")

    def testAddAny(self):
        networks.add_any(self.c)
        actual_networks = self._query('SELECT * FROM network')
        self.assertEquals(
            len(actual_networks),
            1,
            "Additional or missing networks")
        self.assertEquals(actual_networks[0].name, "ANY")
        self.assertEquals(actual_networks[0].ipv4_txt, "0/0")
        self.assertEquals(actual_networks[0].ipv6_txt, "::/0")


def main():
    BaseTestCase.main()

if __name__ == '__main__':
    main()
