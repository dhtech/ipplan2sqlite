from builtins import str
from builtins import object
import re
import sys


class bcolors(object):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def get_tables(
    c,
    exclude=['meta_data',
             'sqlite_sequence'],
        include=['firewall_rule_ip_level']):
    c.execute('''SELECT name FROM sqlite_master WHERE type = 'table';''')
    tables = [t[0] for t in c.fetchall() if t[0] not in exclude]
    tables += include
    return tables


def get_counts(c):
    tables = get_tables(c)
    counts = {}
    for table in tables:
        c.execute('SELECT COUNT(*) FROM %s' % table)
        count = c.fetchone()[0]
        counts[table] = count
    return counts


def get_object_sets(c):
    tables = get_tables(c)
    objects = {}
    for table in tables:
        c.execute('PRAGMA table_info(%s)' % table)
        r = c.fetchall()
        columns = [col[1] for col in r if not 'id' in col[1]]
        if len(columns) == 0:
            objects[table] = set()
            continue
        sql = 'SELECT %s FROM %s' % (','.join(columns), table)
        c.execute(sql)
        objects[table] = set(c.fetchall())
    return objects


def get_state(c):
    state = {}
    state['tables'] = get_tables(c)
    state['objects'] = get_object_sets(c)
    state['counts'] = get_counts(c)
    return state


def _print(color, msg, output):
    output.write(color + msg + bcolors.ENDC + "\n")


def compare_states(before, after, logging, output=sys.stdout, limit=10000):
    # Did we detect _any_ changes?
    changed = False

    # Any new tables?
    tables_before = set(before['tables'])
    tables_after = set(after['tables'])
    dropped_tables = tables_before - tables_after
    new_tables = tables_after - tables_before
    if len(dropped_tables) > 0:
        output.write('Dropped %d table(s):' % (len(dropped_tables)))
        for dropped_table in dropped_tables:
            _print(bcolors.FAIL, dropped_table, output)
        changed = True
    if len(new_tables) > 0:
        output.write('Added %d table(s):' % (len(new_tables)))
        for added_table in new_tables:
            _print(bcolors.OKGREEN, added_table, output)
        changed = True

    # We can only do diff magic on tables that were in both databases
    tables = tables_after.intersection(tables_before)

    # Diff tables
    for table in tables:
        count_before = before['counts'][table]
        objects_before = before['objects'][table]
        count_after = after['counts'][table]
        objects_after = after['objects'][table]

        delta_count = count_after - count_before
        if delta_count != 0:
            logging.info('%s %d' % (table, delta_count))
            changed = True
            removed_objects = objects_before - objects_after
            added_objects = objects_after - objects_before
            if len(removed_objects) > 0:
                i = 0
                for removed_object in removed_objects:
                    _print(bcolors.FAIL, "- " + str(removed_object), output)
                    i += 1
                    if i >= limit:
                        break
            if len(added_objects) > 0:
                i = 0
                for added_object in added_objects:
                    _print(bcolors.OKGREEN, "+ " + str(added_object), output)
                    i += 1
                    if i >= limit:
                        break
