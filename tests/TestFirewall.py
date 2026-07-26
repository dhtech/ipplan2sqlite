import os
import sqlite3
import sys
import unittest
from BaseTestCase import BaseTestCase

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)
import firewall
import networks
import packages
import processor
import tables


class TestFirewall(BaseTestCase, unittest.TestCase):

    def setUp(self):
        super(TestFirewall, self).setUp()
        manifest = self._load_YAML('data/manifest.yml')
        self.packages = manifest['packages']
        networks.add_all(self.c)
        processor.parse(self._load('data/masterNetwork.txt'), self.c)
        firewall.add_services(manifest['services'], self.c)
        firewall.add_flows(manifest['flows'], self.c)
        firewall.add_flows([x.lower() for x in processor.get_domains()], self.c)

    def testServerClientRule(self):
        lines = self._load('data/testServerClientRules.txt')
        processor.parse(lines, self.c)
        packages.build(self.packages, self.c)
        firewall.build(self.packages, self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 1, "Wrong number of firewall rules")

        rule = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM firewall_rule_ip_level"""
        )[0]
        self.assertEquals(
            rule[0],
            'jumpgate1.event.dreamhack.se',
            "Wrong source host")
        self.assertEquals(
            rule[1],
            'ddns1.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(rule[2], 'event', "Wrong flow")
        self.assertEquals(
            rule[3],
            '2022/tcp',
            "Wrong destination port/protocol")

    def testServerClientRuleNat(self):
        lines = self._load('data/testServerClientRulesNat.txt')
        processor.parse(lines, self.c)
        packages.build(self.packages, self.c)
        firewall.build(self.packages, self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 3, "Wrong number of firewall rules")

        non_nat_rule1, nat_rule, non_nat_rule2 = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM firewall_rule_ip_level"""
        )
        self.assertEquals(non_nat_rule1[0], 'jumpgate1.event.dreamhack.se',
            "Wrong source host")
        self.assertEquals(non_nat_rule1[1], 'ddns1.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(non_nat_rule1[2], 'event', "Wrong flow")
        self.assertEquals(non_nat_rule1[3], '2022/tcp',
            "Wrong destination port/protocol")

        self.assertEquals(nat_rule[0], 'nat.event.dreamhack.se',
            "Wrong source host")
        self.assertEquals(nat_rule[1], 'ddns1.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(nat_rule[2], 'event', "Wrong flow")
        self.assertEquals(nat_rule[3], '2022/tcp',
            "Wrong destination port/protocol")

        self.assertEquals(non_nat_rule2[0], 'jumpgate2.event.dreamhack.se',
            "Wrong source host")
        self.assertEquals(non_nat_rule2[1], 'ddns1.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(non_nat_rule2[2], 'event', "Wrong flow")
        self.assertEquals(non_nat_rule2[3], '2022/tcp',
            "Wrong destination port/protocol")

    def testPublicRule(self):
        processor.parse(self._load('data/testPublicRule.txt'), self.c)
        packages.build(self.packages, self.c)
        firewall.build(self.packages, self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 8, "Wrong number of firewall rules")

        rules = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM
               firewall_rule_ip_level
               WHERE from_node_name = 'EVENT@DREAMHACK'"""
        )
        self.assertEquals(len(rules), 2, "Wrong number of firewall rules")

        rule = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM firewall_rule_ip_level
               WHERE from_node_name = 'EVENT@DREAMHACK'
               AND service_dst_ports = '123/udp,123/tcp'"""
        )
        self.assertEquals(len(rule), 1, "Wrong number of firewall rules")

    def testWorldRule(self):
        processor.parse(self._load('data/testWorldRule.txt'), self.c)
        packages.build(self.packages, self.c)
        firewall.build(self.packages, self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 1, "Wrong number of firewall rules")

        rule = self._query(
            """SELECT
               from_node_name, to_node_name, flow_name, service_dst_ports
               FROM firewall_rule_ip_level"""
        )[0]
        self.assertEquals(rule[0], 'ANY', "Wrong source host")
        self.assertEquals(
            rule[1],
            'www.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(rule[2], 'event', "Wrong flow")
        self.assertEquals(
            rule[3],
            '80/tcp',
            "Wrong destination port/protocol")

    def testLocalRule(self):
        processor.parse(self._load('data/testLocalRule.txt'), self.c)
        packages.build(self.packages, self.c)
        firewall.build(self.packages, self.c)
        rules = self._query('SELECT * FROM firewall_rule_ip_level')
        self.assertEquals(len(rules), 1, "Wrong number of firewall rules")

        rule = rules[0]
        self.assertEquals(rule[0], 1, "Wrong rule id")
        self.assertEquals(rule[2], 'EVENT@TECH-SRV-6-JUMPNET',
            "Wrong source host")
        self.assertEquals(
            rule[3],
            '77.80.231.128/28',
            "Wrong source IPv4 address")
        self.assertEquals(
            rule[5],
            'speedtest1mgmt.event.dreamhack.se',
            "Wrong destination host")
        self.assertEquals(
            rule[11],
            '69/udp',
            "Wrong destination port/protocol")

    def testExplicitServiceOptionsAndVersionSuffixes(self):
        # Exercises the legacy explicit s=/c=/w=/l=/p= option path (as
        # opposed to pkg=), a service registered directly on a network
        # node (not just a host), the redundant-flow pruning when a host
        # and its own network both declare the same service, and the
        # "4"/"6"/dash-flow-prefix/default-flow parsing branches.
        processor.parse(self._load('data/testFirewallEdgeCases.txt'), self.c)
        packages.build(self.packages, self.c)
        firewall.build(self.packages, self.c)

        rules = self._query(
            """SELECT * FROM firewall_rule_ip_level
               WHERE to_node_name = 'edge1.event.dreamhack.se'""")
        by_flow_and_service = dict(
            ((r.flow_name, r.service_name), r) for r in rules)

        # local(): l=dhssh6 -> service 'dhssh', version suffix '6'.
        local_rule = by_flow_and_service[('event', 'dhssh')]
        self.assertEquals(
            local_rule.from_node_name,
            'EVENT@TECH-SRV-8-EDGENET',
            "Wrong source for local rule")
        self.assertEquals(local_rule.is_ipv4, 0, "Wrong IPv4 flag")
        self.assertEquals(local_rule.is_ipv6, 1, "Wrong IPv6 flag")

        # world(): w=default-http -> dash-prefixed 'default' flow name
        # resolves to the network's default flow ('event').
        world_rule = by_flow_and_service[('event', 'http')]
        self.assertEquals(
            world_rule.from_node_name, 'ANY', "Wrong source for world rule")
        self.assertEquals(world_rule.is_ipv4, 1, "Wrong IPv4 flag")
        self.assertEquals(world_rule.is_ipv6, 1, "Wrong IPv6 flag")

        # public(): p=http4 -> version suffix '4', one rule per public
        # network.
        public_rules = self._query(
            """SELECT * FROM firewall_rule_ip_level
               WHERE to_node_name = 'edge1.event.dreamhack.se'
               AND service_name = 'http'
               AND from_node_name != 'ANY'""")
        self.assertEquals(
            len(public_rules), 4, "Wrong number of public rules")
        for rule in public_rules:
            self.assertEquals(rule.is_ipv4, 1, "Wrong IPv4 flag")
            self.assertEquals(rule.is_ipv6, 0, "Wrong IPv6 flag")

    def testUnmappedServiceRaises(self):
        processor.parse(
            self._load('data/testFirewallInvalidService.txt'), self.c)
        packages.build(self.packages, self.c)
        self.assertRaises(Exception, firewall.build, self.packages, self.c)


def main():
    BaseTestCase.main()

if __name__ == '__main__':
    main()
