import collections
import re


def split_package_spec(package_spec):
    """Given a string in the format 'test(a,b)' return ('test', 'a,b')."""
    match = re.match('^(.*?)\((.*)\)$', package_spec)
    if match:
        package_name = match.group(1)
        package_options = match.group(2).split(',')
    else:
        package_name = package_spec
        package_options = []
    return package_name, package_options


def build(packages, c):
    # Extract service flows from packages
    c.execute('SELECT node_id, value FROM option WHERE name = ?', ('pkg', ))
    package_options = c.fetchall()

    # Fetch all networks, we want to know if a node_id is a network for
    # default packages.
    c.execute('SELECT node_id FROM network')
    networks = [x[0] for x in c.fetchall()]

    # Fetch all hosts -> net map
    c.execute('SELECT node_id, network_id FROM host')
    netmap = {x[0]: x[1] for x in c.fetchall()}

    nodes = dict()
    for node_id, package_spec in package_options:
        # Seperate options from name
        package_name, package_options = split_package_spec(package_spec)
        if node_id not in nodes:
            nodes[node_id] = collections.defaultdict(list)
        if not package_name:
            continue
        nodes[node_id][package_name].extend(package_options)

    for node_id, packmap in nodes.iteritems():
        packmap = nodes[node_id]
        # For hosts include network packages
        if node_id not in networks and netmap[node_id] in nodes:
            for n, p in nodes[netmap[node_id]].iteritems():
                packmap[n].extend(p)
        # Add "default" to hosts, but not networks
        if '-default' not in packmap and node_id not in networks:
            for package_spec in packages['default']:
                package_name, package_options = split_package_spec(package_spec)
                nodes[node_id][package_name].extend(package_options)

        # Remove blacklisted packages
        for package in [x[1:] for x in packmap if x and x[0] == '-']:
            del packmap['-' + package]
            if package in packmap:
                del packmap[package]

    for node_id, packmap in nodes.iteritems():
        for package, options in sorted(packmap.iteritems()):
            for option in options or [None]:
                row = [node_id, package, option]
                c.execute('INSERT INTO package VALUES (NULL, ?, ?, ?)', row)
