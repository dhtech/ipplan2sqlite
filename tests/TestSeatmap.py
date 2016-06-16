import os
import sqlite3
import sys
import unittest

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))
sys.path.insert(1, path)

import location
import processor

from BaseTestCase import BaseTestCase


class TestSeatmap(BaseTestCase, unittest.TestCase):

  # def setUp(self):
  #   self.seatM

  def testIsValidSeat(self):
    seat = {
        "status": "free",
        "x1": 30,
        "welcome_note_switch": "",
        "dedicated_section": "",
        "section": 31,
        "laststatus": "free",
        "y2": 67,
        "seat": 66,
        "y1": 70,
        "renderorder": 9204,
        "x2": 27,
        "displaystatus": "visible",
        "ref_event": 40,
        "id": 239491,
        "hall": "B",
        "row": "B19"
    }
    self.assertTrue(location.is_valid_seat(seat), "Should be a valid seat")


  def testNormalizeTableName(self):
    self.assertEqual(location.normalize_table_name("B9"), "B09")
    self.assertEqual(location.normalize_table_name("B19"), "B19")


  def testGetHallNameFromTableName(self):
    self.assertEquals(location.get_hall_from_table_name("D19"), "D")
    self.assertEquals(location.get_hall_from_table_name("LN02"), "LN")

  def testAddCoordinatesNoSwitched(self):
    seatmap = self._load_JSON("data/seatsB19.json")
    location.add_coordinates(seatmap, self.c)
    tables = self._query('SELECT * FROM table_coordinates')
    self.assertEquals(len(tables), 0, "Wrong number of tables in database")

  def testAddCoordinates(self):
    seatmap = self._load_JSON("data/seatsB19.json")
    processor.parse(self._load('data/testTableB19.txt'), self.c)
    location.add_coordinates(seatmap, self.c)
    tables = self._query('SELECT * FROM table_coordinates')
    self.assertEquals(len(tables), 1, "Wrong number of tables in database")
    self.assertEquals(tables[0].name, "B19", "Wrong table name")
    self.assertEquals(tables[0].hall, "B", "Wrong hall name")
    self.assertEquals(tables[0].x1, 0, "Wrong x1 coordinate")
    self.assertEquals(tables[0].y1, 8, "Wrong y1 coordinate")
    self.assertEquals(tables[0].y2, 0, "Wrong y2 coordinate")
    self.assertEquals(tables[0].x_start, 0, "Wrong x_start coordinate")
    self.assertEquals(tables[0].y_start, 3, "Wrong y_start coordinate")
    self.assertEquals(tables[0].width, 158, "Wrong width")
    self.assertEquals(tables[0].height, 8, "Wrong height")
    self.assertEquals(tables[0].horizontal, 1, "Wrong horizontal flag")


  def testSwitchLocation(self):
    seatmap = self._load_JSON("data/seatsB19.json")
    processor.parse(self._load('data/testTableB19.txt'), self.c)
    location.add_coordinates(seatmap, self.c)
    switches = self._query('SELECT * FROM switch_coordinates')
    self.assertEquals(len(switches), 2, "Wrong number of switches in database")
    self.assertEquals(
      switches[0].name,
      "b19-a.event.dreamhack.local",
      "Wrong switch name")
    self.assertEquals(switches[0].x, 118.5, "Wrong x coordinate")
    self.assertEquals(switches[0].y, 4, "Wrong y coordinate")
    self.assertEquals(switches[0].table_name, "B19", "Wrong table name")

    self.assertEquals(
      switches[1].name,
      "b19-b.event.dreamhack.local",
      "Wrong switch name")
    self.assertEquals(switches[1].x, 39.5, "Wrong x coordinate")
    self.assertEquals(switches[1].y, 4, "Wrong y coordinate")
    self.assertEquals(switches[1].table_name, "B19", "Wrong table name")

  def testSwitchLocationWithMixedLayout(self):
    seatmap = self._load_JSON("data/seatsB19_C19.json")
    processor.parse(self._load('data/testTableB19_C19.txt'), self.c)
    location.add_coordinates(seatmap, self.c)
    switches = self._query('SELECT * FROM switch_coordinates')
    self.assertEquals(len(switches), 5, "Wrong number of switches in database")

    self.assertEquals(
      switches[0].name,
      "c19-a.event.dreamhack.local",
      "Wrong switch name")
    self.assertEquals(switches[0].x, 4, "Wrong x coordinate")
    self.assertEquals(switches[0].y, 129.66666666666666, "Wrong y coordinate")
    self.assertEquals(switches[0].table_name, "C19", "Wrong table name")

    self.assertEquals(
      switches[1].name,
      "c19-b.event.dreamhack.local",
      "Wrong switch name")
    self.assertEquals(switches[1].x, 4, "Wrong x coordinate")
    self.assertEquals(switches[1].y, 77, "Wrong y coordinate")
    self.assertEquals(switches[1].table_name, "C19", "Wrong table name")

    self.assertEquals(
      switches[2].name,
      "c19-c.event.dreamhack.local",
      "Wrong switch name")
    self.assertEquals(switches[2].x, 4, "Wrong x coordinate")
    self.assertEquals(switches[2].y, 24.333333333333332, "Wrong y coordinate")
    self.assertEquals(switches[2].table_name, "C19", "Wrong table name")

    self.assertEquals(
      switches[3].name,
      "b19-a.event.dreamhack.local",
      "Wrong switch name")
    self.assertEquals(switches[3].x, 118.5, "Wrong x coordinate")
    self.assertEquals(switches[3].y, 4, "Wrong y coordinate")
    self.assertEquals(switches[3].table_name, "B19", "Wrong table name")

    self.assertEquals(
      switches[4].name,
      "b19-b.event.dreamhack.local",
      "Wrong switch name")
    self.assertEquals(switches[4].x, 39.5, "Wrong x coordinate")
    self.assertEquals(switches[4].y, 4, "Wrong y coordinate")
    self.assertEquals(switches[4].table_name, "B19", "Wrong table name")



def main():
    BaseTestCase.main()

if __name__ == '__main__':
    main()
