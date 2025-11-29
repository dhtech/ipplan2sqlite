import logging
import re
from collections import namedtuple

Rectangle = namedtuple(
    'Rectangle', ['x1', 'x2', 'y1', 'y2', 'x_start', 'y_start',
                  'width', 'height', 'horizontal'])

Dot = namedtuple('Dot', ['x', 'y'])


def even(x):
    return round(x/2.)*2


def is_valid_seat(seat):
    return all (key in seat for key in ("row", "seat", "x1", "x2", "y1", "y2"))

def is_hall_position(seat):
    return all (key in seat for key in ("hall", "type", "x", "y"))

def get_hall_from_table_name(table):
    match = re.search(r'([A-Za-z]+)[0-9]+', table)
    if match:
        return match.group(1)
    raise ValueError(f"Invalid table name: {table}")

def normalize_table_name(table):
    table = table.strip()
    match = re.search(r'([A-Za-z]+)([0-9]+)', table)
    if not match:
        raise ValueError(f"Invalid table name: {table}")

    hall, row = match.group(1, 2)
    return f"{hall.upper()}{int(row):02}"

def add_coordinates(seatmap, cursor):
    halls = {}
    tables = {}
    for seat in seatmap:
        if not is_valid_seat(seat):
            if is_hall_position(seat):
                hall = seat['hall']
                cursor.execute("INSERT INTO hall_positions VALUES (?,?,?)", (seat['hall'], seat['x'], seat['y']))
            continue
        table = normalize_table_name(seat['row'])
        logging.debug("Normalized table name %s to %s", seat['row'], table)
        hall = seat['hall']
        halls.setdefault(hall, []).append(seat)
        tables.setdefault(hall, {}).setdefault(table, []).append(seat)

    switches = switches_by_table(cursor)

    table_coordinates = {}
    scales = []
    for hall in halls:
        table_coordinates[hall] = []
        for table in sorted(tables[hall].keys(), key=lambda x: (len(x), x)):
            if not switches.get(table, []):
              logging.debug("Table %s has no switches, ignoring", table)
              continue
            c, scale = table_location(table, tables, hall)
            scales.append(scale)
            table_coordinates[hall].append((table, c))

    scale = sorted(scales)[len(scales) // 2] if scales else 1.0
    logging.debug("Selected median scale %f", scale)

    for hall in halls:
        x_min = float("inf")
        y_max = 0
        y_min = float("inf")

        scaled_table_coordinates = []
        for table, c in table_coordinates[hall]:
            s = Rectangle(
                    even(c.x1 * scale),
                    even(c.x2 * scale),
                    even(c.y1 * scale),
                    even(c.y2 * scale),
                    even(c.x_start * scale),
                    even(c.y_start * scale),
                    even(c.width * scale),
                    even(c.height * scale),
                    c.horizontal)
            x_min = s.x1 if s.x1 < x_min else x_min
            x_min = s.x2 if s.x2 < x_min else x_min
            y_max = s.y1 if s.y1 > y_max else y_max
            y_max = s.y2 if s.y2 > y_max else y_max
            y_min = s.y1 if s.y1 < y_min else y_min
            y_min = s.y2 if s.y2 < y_min else y_min
            scaled_table_coordinates.append((table, s))

        x_offset = x_min
        y_offset = y_min
        logging.debug("Hall %s has offset [%f, %f]", hall, x_offset, y_offset)

        for table, t in scaled_table_coordinates:
            coordinates = c = Rectangle(
                t.x1 - x_offset, t.x2 - x_offset, t.y1 - y_offset,
                t.y2 - y_offset, t.x_start -
                x_offset, t.y_start - y_offset,
                t.width, t.height, t.horizontal)
            row = [table, hall, c.x1, c.x2, c.y1, c.y2, c.x_start, c.y_start,
                   c.width, c.height, c.horizontal]
            cursor.execute(
                """INSERT INTO table_coordinates
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                row)
            switch_order = sorted(switches[table])
            n = len(switches.get(table, []))
            locations = zip(
                switch_order, switch_locations(coordinates, n))
            for switch_name, location in locations:
                row = [switch_name, location[0], location[1], table]
                cursor.execute(
                    'INSERT INTO switch_coordinates VALUES(?, ?, ?, ?)',
                    row)


def switch_locations(t, n):
    locations = []

    if t.horizontal:
        for i in range(1, 2 * n, 2):
            x = t.x_start + (t.width / n) / 2 * i
            y = t.y_start - t.height / 2
            locations.append((x,y))
    else:
        for i in range(1, 2 * n, 2):
            x = t.x_start - t.height / 2
            y = t.y_start + (t.width / n) / 2 * i
            locations.append((x,y))

    return locations


def table_location(table, tables, hall):
    seats = sorted(
        tables[hall][table],
        key=lambda seat: int(seat['seat']))
    logging.debug("First and last seat on %s is %s and %s",
            table, seats[0]["seat"], seats[-1]["seat"])

    x1 = int(seats[0]["x1"])
    x2 = int(seats[-1]["x2"])
    y1 = int(seats[0]["y1"])
    y2 = int(seats[-1]["y2"])

    x_len = max(x1, x2) - min(x1, x2)
    y_len = max(y1, y2) - min(y1, y2)

    x_start = min(x1, x2)
    y_start = min(y1, y2)
    horizontal = 1 if x_len > y_len else 0

    # Calculate scaling. A normal table is 33x2 seats, use the classical
    # magial measurement of 157x2 and scale to that
    length = x_len if horizontal else y_len
    seats = len(seats)/2  # Assume 2xY seating
    scale = 1.0 / ((float(length) * 33.0/float(seats))/ 157.0)
    logging.debug("Bounding box for table %s is [%d, %d - %d, %d], scale is %f",
            table, x1, y1, x2, y2, scale)

    width = x_len if horizontal else y_len
    height = y_len if horizontal else x_len

    return Rectangle(x1, x2, y1, y2, x_start, y_start, width, height,
                     horizontal), scale


def switches_by_table(cursor):
    switches = {}
    sql = '''SELECT switch_name FROM active_switch'''
    for switch in cursor.execute(sql).fetchall():
        table = switch[0].split('-')[0].upper()
        table = table[0] + table[1:]
        switches[table] = switches.get(table, [])
        switches[table].append(switch[0])
    for table in switches.keys():
        logging.debug("Table %s has %d switches", table, len(switches[table]))
    return switches
