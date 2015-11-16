#!/usr/bin/env python2

import argparse
import datetime
import json
import logging
import os
import platform
import re
import sqlite3
import sys
import yaml

from lib import diff
from lib import firewall
from lib import location
from lib import networks
from lib import packages
from lib import processor
from lib import statistics
from lib import tables

def generate(database, manifest_file, seatmap_file,
             revision=None, current_event=None, ipplans=()):
  logging.debug('Using Python %s', platform.python_version())

  # Create fresh database file
  logging.debug('Checking if database file %s exists', database)
  has_previous_db = False
  previous_statistics = None
  if os.path.isfile(database):
      logging.debug(
          'Found existing database file %s, gathering stats before deleting',
          database)
      try:
          conn = sqlite3.connect(database)
          c = conn.cursor()
          before = diff.get_state(c)
          logging.debug(
              'Gathered stats for previous database file \'%s\'', database)
          has_previous_db = True
      except Exception as e:
          logging.debug(
              'Could not gather stats for previous database file \'%s\'.',
              database)
      try:
          os.unlink(database)
      except Exception as e:
          logging.error(
              'Could not delete previous database file %s',
              database)
          sys.exit(2)
  try:
      conn = sqlite3.connect(database)
      c = conn.cursor()
      c.execute('SELECT SQLITE_VERSION()')
      data = c.fetchone()
      logging.debug("SQLite version: %s", data[0])
      # Add meta data
  except sqlite3.Error as e:
      logging.error('Error when opening database %s: %s', database, e)
      sys.exit(3)

  # Create tables
  logging.debug('Creating database tables')
  tables.create(conn)

  # Add meta data
  if revision:
      c.execute("""INSERT INTO meta_data VALUES ('revision', '%d')""" %
              int(revision))
  if not current_event is None:
      c.execute(
          "INSERT INTO meta_data VALUES ('current_event', ?)",
          (current_event,))
  c.execute("""INSERT INTO meta_data VALUES ('time_generated', '%s')""" %
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


  # Read the ipplan file
  for ipplan in ipplans:
    logging.debug('Checking if ipplan file %s exists', ipplan)
    if not os.path.isfile(ipplan):
        logging.error('No such ipplan file: %s', ipplan)
        sys.exit(4)
    logging.debug('Found ipplan file %s', ipplan)

    # Parse ipplan
    logging.debug('Parsing lines in %s', ipplan)
    try:
        with open(ipplan, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        logging.error('Could not parse ipplan file %s: %s', ipplan, e)

    # Parse ipplan
    logging.debug('Parsing ipplan')
    processor.parse(lines, c)

  # Add custom networks
  logging.debug('Adding custom networks')
  networks.add_all(c)

  # Read the manifest file
  logging.debug('Checking if manifest file %s exists', manifest_file)
  if not os.path.isfile(manifest_file):
      logging.error('No such manifest file: %s', manifest_file)
      sys.exit(5)
  logging.debug('Found manifest file %s', manifest_file)
  logging.debug('Parsing manifest file as JSON')
  try:
      with open(manifest_file, 'r') as f:
          manifest = yaml.safe_load(f.read())
  except Exception as e:
      logging.error(
          'Could not parse manifest file %s as JSON: %s',
          manifest_file, e)
      sys.exit(6)

  # Add manifest to database
  logging.debug('Adding manifest to database')
  try:
      firewall.add_services(manifest['services'], c)
  except Exception as e:
      logging.error('Could not add services to database: %s', e)

  # Add flows to database
  try:
      firewall.add_flows(manifest['flows'], c)
      firewall.add_flows([x.lower() for x in processor.get_domains()], c)
  except Exception as e:
      logging.error('Could not add flows to database: %s', e)
      sys.exit(8)

  # Register packages
  logging.debug('Building packages table')
  packages.build(manifest['packages'], c)

  # Build firewall
  logging.debug('Building firewall rules')
  firewall.add_packages(manifest['packages'], c)
  firewall.build(c)

  # Support running without seatmap for validation and testing purposes
  if seatmap_file:
      # Read the seat map file
      logging.debug('Checking of seatmap file \'%s\' exists', seatmap_file)
      if not os.path.isfile(seatmap_file):
          logging.error('No such seatmap file: \'%s\'', seatmap_file)
          sys.exit(9)
      logging.debug('Found seatmap file \'%s\'', seatmap_file)
      logging.debug('Parsing seatmap file as JSON')
      try:
          with open(seatmap_file, 'r') as f:
              seatmap = json.loads(f.read())
      except Exception as e:
          logging.error(
              'Could not parse seatmap file \'%s\' as JSON: %s',
              seatmap_file, e)

      # Build location mapping
      location.add_coordinates(seatmap, c)

  # Diff the database before and after
  if has_previous_db:
      after = diff.get_state(c)
      diff.compare_states(before, after, logging)

  # Close database file
  logging.debug('Committing database')
  try:
      conn.commit()
  except Exception as e:
      logging.error('Could not commit database \'%s\': %s', args.database, e)
      sys.exit(9)

  logging.debug('Closing database')
  try:
      conn.close()
  except Exception as e:
      logging.error('Could not close database \'%s\': %s', args.database, e)
      sys.exit(10)

if __name__ == '__main__':
  # Parse command line arguments
  args_parser = argparse.ArgumentParser()
  args_parser.add_argument("--debug", action="store_true",
      help="Increase output verbosity")
  args_parser.add_argument("--database", required=True,
      help="Path to final SQLite database")
  args_parser.add_argument("--manifest", required=True,
      help="Path to manifest file")
  args_parser.add_argument("--seatmap", required=False,
      help="Path to seatmap file")
  args_parser.add_argument("--revision", required=False,
      help="Which Subversion revision that triggered the generation")
  args_parser.add_argument("--current_event", required=False,
      help="The event the database is generated for")
  args_parser.add_argument('ipplans', metavar='ipplan', nargs='+',
      help='ipplan file')
  args = args_parser.parse_args()

  # Set up logging
  root = logging.getLogger()
  ch = logging.StreamHandler(sys.stdout)
  formatter = logging.Formatter(
      '%(asctime)s - ipplan2sqlite - %(levelname)s - %(message)s')
  ch.setFormatter(formatter)
  root.addHandler(ch)

  # Adjust logging to desired verbosity
  if args.debug:
      ch.setLevel(logging.DEBUG)
      root.setLevel(logging.DEBUG)
  else:
      ch.setLevel(logging.INFO)
      root.setLevel(logging.INFO)

  generate(args.database, args.manifest, args.seatmap,
           args.revision, args.current_event, args.ipplans)
