import os
import sqlite3
import sys
import unittest

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)

import processor
import packages

from BaseTestCase import BaseTestCase


class TestPackages(BaseTestCase, unittest.TestCase):

  def testPackagesLogic(self):
    processor.parse(self._load('data/testParsePackages.txt'), self.c)
    packages.build(self._load_YAML('data/manifest.yml')['packages'], self.c)
    pack = self._query('SELECT * FROM package')
    self.assertEquals(len(pack), 26, "Wrong number of packages in database")
    expected = (
            (1, 'dns', None),
            (2, 'dhssh', 'test'),
            (2, 'dns', None),
            (2, 'ldapclient', None),
            (2, 'syslogclient', None),
            (2, 'tac', '(test)'),
            (3, 'dns', None),
            (5, 'dhssh', 'test'),
            (5, 'ldapclient', None),
            (5, 'syslogclient', None),
            (5, 'tac', 'a,b'),
            (6, 'dhssh', 'test'),
            (6, 'dns', None),
            (6, 'ldapclient', None),
            (6, 'syslogclient', None),
            (6, 'wwwpub', None),
            (8, 'dhssh', 'test'),
            (8, 'ldapclient', None),
            (8, 'syslogclient', None),
            (8, 'tac', None),
            (10, 'dhssh', 'test'),
            (10, 'ldapclient', None),
            (10, 'syslogclient', None),
            (11, 'dhssh', 'test'),
            (11, 'ldapclient', None),
            (11, 'syslogclient', None))
    for i, (node_id, package, options) in enumerate(expected):
        self.assertEquals(pack[i].node_id, node_id)
        self.assertEquals(pack[i].name, package)
        self.assertEquals(pack[i].options, options)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
