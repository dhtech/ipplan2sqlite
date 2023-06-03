from builtins import object
import json
import logging
import os
import sqlite3
import sys
import unittest
import yaml

from collections import namedtuple

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)
import processor
import tables


def namedtuple_factory(cursor, row):
    fields = [col[0] for col in cursor.description]
    Row = namedtuple("Row", fields)
    return Row(*row)


class BaseTestCase(object):

    def _query(self, q):
        return self.c.execute(q).fetchall()

    def _load(self, f):
        f = os.path.abspath(os.path.join(os.path.dirname(__file__), f))
        with open(f, 'r') as f:
            lines = f.readlines()
        return lines

    def _load_JSON(self, f):
        f = os.path.abspath(os.path.join(os.path.dirname(__file__), f))
        with open(f, 'r') as f:
            data = json.load(f)
        return data

    def _load_YAML(self, f):
        f = os.path.abspath(os.path.join(os.path.dirname(__file__), f))
        with open(f, 'r') as f:
            data = yaml.load(f.read())
        return data

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = namedtuple_factory
        self.c = self.conn.cursor()
        tables.create(self.conn)
        logging.info('Setting up %s', self._testMethodName)

    def tearDown(self):
        self.conn.close()
        self.c = None

    @staticmethod
    def main():
        # Set up logging
        root = logging.getLogger()
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
                '%(asctime)s - ipplan2sqlite - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        root.addHandler(ch)
        ch.setLevel(logging.DEBUG)
        root.setLevel(logging.DEBUG)
        unittest.main()
