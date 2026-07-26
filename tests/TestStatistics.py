import os
import sys
import unittest
from BaseTestCase import BaseTestCase

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)

import statistics


class TestStatistics(BaseTestCase, unittest.TestCase):

    def setUp(self):
        super(TestStatistics, self).setUp()
        # gather_all() runs unaliased "SELECT COUNT(*)" queries, which the
        # namedtuple row factory from BaseTestCase can't handle (as in
        # production, statistics.py is always called with a plain cursor).
        self.c.row_factory = None

    def testGatherAllEmptyDatabase(self):
        results = statistics.gather_all(self.c)
        self.assertEquals(results['nbr_of_nodes'], 0)
        self.assertEquals(results['nbr_of_hosts'], 0)
        self.assertEquals(results['nbr_of_networks'], 0)
        self.assertEquals(results['nbr_of_firewall_rules'], 0)
        self.assertEquals(results['nbr_of_switches'], 0)
        self.assertEquals(results['nbr_of_active_switches'], 0)

    def testGatherAllWithData(self):
        self.c.execute('INSERT INTO node VALUES (NULL)')
        self.c.execute('INSERT INTO node VALUES (NULL)')
        self.c.execute(
            """INSERT INTO host (node_id, name)
               VALUES (1, 'h1.event.dreamhack.se')""")
        self.c.execute(
            "INSERT INTO network (node_id, name) VALUES (2, 'EVENT@C01')")
        self.c.execute("INSERT INTO service (name) VALUES ('ssh')")
        self.c.execute("INSERT INTO flow (name) VALUES ('event')")
        self.c.execute(
            """INSERT INTO firewall_rule
               (from_node_id, to_node_id, service_id, flow_id,
                is_ipv4, is_ipv6)
               VALUES (1, 2, 1, 1, 1, 0)""")

        results = statistics.gather_all(self.c)
        self.assertEquals(results['nbr_of_nodes'], 2)
        self.assertEquals(results['nbr_of_hosts'], 1)
        self.assertEquals(results['nbr_of_networks'], 1)
        self.assertEquals(results['nbr_of_firewall_rules'], 1)
        self.assertEquals(results['nbr_of_switches'], 0)
        self.assertEquals(results['nbr_of_active_switches'], 0)

    def testPrintAllIsANoop(self):
        # print_all() is currently a stub; make sure it stays callable
        # without raising for any input.
        self.assertEquals(
            statistics.print_all({'nbr_of_nodes': 1}, {'nbr_of_nodes': 0}),
            None)


def main():
    BaseTestCase.main()

if __name__ == '__main__':
    main()
