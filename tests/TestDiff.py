import os
import sys
import unittest
from BaseTestCase import BaseTestCase

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)

import diff


class FakeLogging(object):

    def __init__(self):
        self.messages = []

    def info(self, msg, *args):
        self.messages.append(msg % args if args else msg)


class TestDiff(BaseTestCase, unittest.TestCase):

    def setUp(self):
        super(TestDiff, self).setUp()
        # get_counts() runs unaliased "SELECT COUNT(*)" queries, which the
        # namedtuple row factory from BaseTestCase can't handle (as in
        # production, diff.py is always called with a plain cursor).
        self.c.row_factory = None

    def testGetTables(self):
        tables = diff.get_tables(self.c)
        self.assertTrue('node' in tables, "Missing real table")
        self.assertTrue('host' in tables, "Missing real table")
        self.assertFalse('meta_data' in tables, "meta_data should be excluded")
        self.assertFalse(
            'sqlite_sequence' in tables, "sqlite_sequence should be excluded")
        self.assertTrue(
            'firewall_rule_ip_level' in tables, "Missing included view")

    def testGetCounts(self):
        self.c.execute('INSERT INTO node VALUES (NULL)')
        self.c.execute(
            "INSERT INTO host (node_id, name) VALUES (1, 'h1')")
        counts = diff.get_counts(self.c)
        self.assertEquals(counts['node'], 1)
        self.assertEquals(counts['host'], 1)
        self.assertEquals(counts['network'], 0)
        self.assertEquals(counts['firewall_rule_ip_level'], 0)

    def testGetObjectSetsWithOnlyIdColumn(self):
        # The 'node' table only has an 'id' column, which get_object_sets
        # filters out entirely, leaving no columns to select.
        objects = diff.get_object_sets(self.c)
        self.assertEquals(objects['node'], set())

    def testGetObjectSetsWithColumns(self):
        self.c.execute(
            """INSERT INTO service (name, description, dst_ports, src_ports)
               VALUES ('ssh', 'Secure Shell', '22/tcp', '')""")
        objects = diff.get_object_sets(self.c)
        self.assertEquals(
            objects['service'], set([('ssh', 'Secure Shell', '22/tcp', '')]))

    def testGetState(self):
        self.c.execute('INSERT INTO node VALUES (NULL)')
        state = diff.get_state(self.c)
        self.assertEquals(set(state.keys()), set(['tables', 'objects', 'counts']))
        self.assertEquals(state['counts']['node'], 1)
        self.assertTrue('node' in state['tables'])
        self.assertTrue('node' in state['objects'])

    def testCompareStatesNoChanges(self):
        state = {
            'tables': ['node'],
            'counts': {'node': 1},
            'objects': {'node': set([('a',)])},
        }
        log = FakeLogging()
        output = StringIO()
        diff.compare_states(state, state, log, output=output)
        self.assertEquals(output.getvalue(), '')
        self.assertEquals(log.messages, [])

    def testCompareStatesDroppedAndAddedTables(self):
        before = {
            'tables': ['node', 'old_table'],
            'counts': {'node': 1, 'old_table': 0},
            'objects': {'node': set(), 'old_table': set()},
        }
        after = {
            'tables': ['node', 'new_table'],
            'counts': {'node': 1, 'new_table': 0},
            'objects': {'node': set(), 'new_table': set()},
        }
        log = FakeLogging()
        output = StringIO()
        diff.compare_states(before, after, log, output=output)
        result = output.getvalue()
        self.assertTrue('Dropped 1 table(s)' in result)
        self.assertTrue('old_table' in result)
        self.assertTrue('Added 1 table(s)' in result)
        self.assertTrue('new_table' in result)

    def testCompareStatesRemovedObjects(self):
        before = {
            'tables': ['node'],
            'counts': {'node': 2},
            'objects': {'node': set([('a',), ('b',)])},
        }
        after = {
            'tables': ['node'],
            'counts': {'node': 1},
            'objects': {'node': set([('a',)])},
        }
        log = FakeLogging()
        output = StringIO()
        diff.compare_states(before, after, log, output=output)
        self.assertTrue("- ('b',)" in output.getvalue())
        self.assertEquals(log.messages, ['node -1'])

    def testCompareStatesAddedObjects(self):
        before = {
            'tables': ['node'],
            'counts': {'node': 1},
            'objects': {'node': set([('a',)])},
        }
        after = {
            'tables': ['node'],
            'counts': {'node': 2},
            'objects': {'node': set([('a',), ('b',)])},
        }
        log = FakeLogging()
        output = StringIO()
        diff.compare_states(before, after, log, output=output)
        self.assertTrue("+ ('b',)" in output.getvalue())
        self.assertEquals(log.messages, ['node 1'])

    def testCompareStatesRespectsLimit(self):
        before = {
            'tables': ['node'],
            'counts': {'node': 3},
            'objects': {'node': set([('a',), ('b',), ('c',)])},
        }
        after = {
            'tables': ['node'],
            'counts': {'node': 0},
            'objects': {'node': set()},
        }
        log = FakeLogging()
        output = StringIO()
        diff.compare_states(before, after, log, output=output, limit=1)
        self.assertEquals(output.getvalue().count("- ("), 1)

    def testCompareStatesRespectsLimitForAddedObjects(self):
        before = {
            'tables': ['node'],
            'counts': {'node': 0},
            'objects': {'node': set()},
        }
        after = {
            'tables': ['node'],
            'counts': {'node': 3},
            'objects': {'node': set([('a',), ('b',), ('c',)])},
        }
        log = FakeLogging()
        output = StringIO()
        diff.compare_states(before, after, log, output=output, limit=1)
        self.assertEquals(output.getvalue().count("+ ("), 1)


def main():
    BaseTestCase.main()

if __name__ == '__main__':
    main()
