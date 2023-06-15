import os
import sqlite3
import sys
import unittest

from tests.BaseTestCase import BaseTestCase

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)

from lib import processor
from lib import packages

class TestPackages(BaseTestCase, unittest.TestCase):

  def testPackagesLogic(self):
    processor.parse(self._load('data/testParsePackages.txt'), self.c)
    packages.build(self._load_YAML('data/manifest.yml')['packages'], self.c)
    pack = self._query('SELECT * FROM package')
    expected = (
            (1, 'dns', 'last'),
            (2, 'dhssh', 'test'),
            (2, 'dns', '(test)'),
            (2, 'dns', 'last'),
            (2, 'ldapclient', None),
            (2, 'syslogclient', None),
            (3, 'dns', 'last'),
            (5, 'dhssh', 'test'),
            (5, 'tac', 'a'),
            (5, 'tac', 'b'),
            (6, 'dhssh', 'test'),
            (6, 'dns', None),
            (6, 'wwwpub', None),
            (8, 'dhssh', 'test'),
            (8, 'syslogclient', None),
            (8, 'tac', None),
            (9, 'dhssh', 'test'),
            (9, 'syslogclient', None),
            (10, 'dhssh', 'test'),
            (10, 'ldapclient', None),
            (10, 'syslogclient', None),
            (11, 'dhssh', 'test'),
            (11, 'syslogclient', None),
            (15, 'switch', None))
    self.assertEquals(len(pack), len(expected),
            "Wrong number of packages in database: got %d, expected %d" % (
                len(pack), len(expected)))
    for i, (node_id, package, option) in enumerate(expected):
        self.assertEquals(pack[i].node_id, node_id)
        self.assertEquals(pack[i].name, package)
        self.assertEquals(pack[i].option, option)


def main():
    BaseTestCase.main()

if __name__ == '__main__':
    main()
