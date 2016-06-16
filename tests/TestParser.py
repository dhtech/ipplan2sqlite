import os
import sqlite3
import sys
import unittest
from BaseTestCase import BaseTestCase

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)

import processor

class TestParser(BaseTestCase, unittest.TestCase):

    def testParseIPv4(self):
        self.assertEquals(processor.ip2long('8.8.8.8', 4), 134744072)
        self.assertEquals(processor.ip2long('77.80.251.247/32', 4), 1297153015)

    def testParserMapping(self):
        l = ["""#$ d20--b.event.dreamhack.local\t\t\t10.0.3.45
                \t\t\tipv4f;ipv4r;tblswmgmt"""]
        self.assertEquals(
            processor.parser_func(
                l
            ),
            "host"
        )
        l = ["""TECH-SRV-1-INT
                D-FW-V          77.80.231.0/27          921     othernet"""]
        self.assertEquals(
            processor.parser_func(
                l
            ),
            "network"
        )
        self.assertEquals(
            processor.parser_func(["""#@ IPV4-NET      77.80.128.0/17"""]),
            "master_network")

    def testParseMasterNetwork(self):
        processor.parse(self._load('data/testParseMasterNetwork.txt'), self.c)
        networks = self._query('SELECT * FROM network')
        self.assertEquals(len(networks), 1, "Missing master network")
        self.assertEquals(networks[0].node_id, 1, "Wrong node id")
        self.assertEquals(networks[0].name, 'EVENT@DREAMHACK',
            "Wrong network name")

    def testParseNetworkAndHost(self):
        processor.parse(self._load('data/testParseNetworkAndHost.txt'), self.c)

        self.assertEquals(
            self._query('SELECT COUNT(*) as nbr_of_nodes FROM node')[0][0],
            2,
            "Wrong number of nodes")

        host = self._query('SELECT * FROM host')[0]
        self.assertEquals(host.node_id, 2, "Wrong node id")
        self.assertEquals(
            host.name,
            'ddns1.event.dreamhack.se',
            "Wrong hostname")
        self.assertEquals(host.ipv4_addr, 1297147849, "Wrong IPv4 long")
        self.assertEquals(host.ipv4_addr_txt, '77.80.231.201', "Wrong IPv4 address")
        self.assertEquals(
            host.ipv6_addr_txt,
            '2001:67c:24d8:921::201',
            "Wrong IPv6 address")
        self.assertEquals(host.network_id, 1, "Wrong network id")

        options = self._query('SELECT * FROM option')
        self.assertEquals(len(options), 16, "Wrong number of options")
        correct_options = set(
            ['ipv4f',
             'ipv4r',
             'ipv6f',
             'ipv6f',
             'p',
             's',
             'c',
             'othernet'])
        parsed_options = set([str(o[2]) for o in options])
        self.assertEquals(
            len(correct_options.union(parsed_options)),
            8,
            "Missing or additional options")

    def testParseNetworkAndHostNoVlan(self):
        processor.parse(
            self._load('data/testParseNetworkAndHostNoVlan.txt'), self.c)

        host = self._query('SELECT * FROM host')[0]
        self.assertEquals(host.ipv4_addr, 1297147849, "Wrong IPv4 long")
        self.assertEquals(host.ipv4_addr_txt, '77.80.231.201', "Wrong IPv4 address")
        self.assertEquals(host.ipv6_addr_txt, None, "Has an IPv6 address")
        self.assertEquals(host.network_id, 1, "Wrong network id")


    def testParseNetwork(self):
        network_line = """TECH-SRV-1-INT
                          D-FW-V          77.80.231.0/27
                          921     othernet"""
        vlan = processor.network(network_line.split(), self.c, None)
        network = self._query('SELECT * FROM network')[0]
        self.assertEquals(network.node_id, 1, "Wrong node id")
        self.assertEquals(network.name, 'EVENT@TECH-SRV-1-INT', "Wrong network name")
        self.assertEquals(network.vlan, 921, "Wrong VLAN")
        self.assertEquals(network.terminator, 'D-FW-V', "Wrong terminator")
        self.assertEquals(network.ipv4, 1297147648, "Wrong IPv4 long")
        self.assertEquals(network.ipv4_txt, "77.80.231.0/27", "Wrong IPv4 address")
        self.assertEquals(
            network[7],
            "2001:67c:24d8:921::/64",
            "Wrong IPv6 address")
        self.assertEquals(network.ipv4_netmask, 4294967264, "Wrong IPv4 netmask long")
        self.assertEquals(
            network.ipv4_netmask_txt,
            "255.255.255.224",
            "Wrong IPv4 netmask")
        self.assertEquals(network.ipv6_netmask_txt, "64", "Wrong IPv6 netmask decimal")
        self.assertEquals(network.ipv4_gateway, 1297147649, "Wrong IPv4 gateway long")
        self.assertEquals(
            network.ipv4_gateway_txt,
            "77.80.231.1",
            "Wrong IPv4 gateway address ")
        self.assertEquals(
            network.ipv6_gateway_txt,
            "2001:67c:24d8:921::1",
            "Wrong IPv6 gateway address")
        self.assertEquals(network.ipv4_netmask_dec, 27, "Wrong IPv4 netmask decimal")
        self.assertEquals(network.ipv6_capable, 1, "Wrong IPv6 capability")

    def testParseNetworkNoVlan(self):
        network_line = """TECH-SRV-1-INT
                          D-FW-V          77.80.231.0/27
                          -     othernet"""
        vlan = processor.network(network_line.split(), self.c, None)
        network = self._query('SELECT * FROM network')[0]
        self.assertEquals(network.vlan, None, "Has VLAN")
        self.assertEquals(network[7], None, "Has IPv6 address")
        self.assertEquals(network.ipv6_netmask_txt, None, "Has IPv6 netmask decimal")
        self.assertEquals(network.ipv6_gateway_txt, None, "Has IPv6 gateway address")
        self.assertEquals(network.ipv6_capable, 0, "Wrong IPv6 capability")


def main():
    BaseTestCase.main()

if __name__ == '__main__':
    main()
