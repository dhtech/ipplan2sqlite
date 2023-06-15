from __future__ import print_function
from __future__ import absolute_import
from builtins import str
from . import ipcalc
import logging
import re
import socket
import struct
import sys
from binascii import hexlify

MODULE = sys.modules[__name__]

SYNTAX = {
  "^#@": "master_network",
  "^#\$": "host",
  "^[A-Z]": "network"
}

_current_domain = None
_current_v6_base = None
_domains = set()

def get_domains():
  return list(_domains)

def master_network(l, c, r):
    global _current_domain
    global _current_v6_base
    if r is not None:
        node_id = node(c)
        short_name = 'DREAMHACK'
        vlan = 0
        terminator = ''

        # Set current domain
        domain = re.match(r'IPV4-([A-Z0-9]+)-NET', r[1]).group(1).upper()
        _current_domain = domain
        _domains.add(domain)

        # IPv4
        ipv4 = r[2]
        net_ipv4 = ipcalc.Network(ipv4)
        ipv4_gateway = net_ipv4[1]
        ipv4_netmask = str(net_ipv4.netmask())
        ipv4_netmask_dec = int(str(r[2]).split("/")[1])

        # IPv6
        ipv6 = l[2]
        _current_v6_base = ipv6.split('::', 1)[0]

        last_digits = int(str(ipv4_gateway).split('.')[-1])
        ipv6_netmask = int(ipv6.split('/', 1)[1])
        ipv6_gateway = "%s::1" % (_current_v6_base, )

        name = '%s@%s' % (_current_domain, short_name)

        row = [node_id, name, short_name, vlan, terminator, ip2long(ipv4, 4),
               str(ipv4), str(ipv6), ip2long(
                   ipv4_netmask, 4), str(ipv4_netmask),
               str(ipv6_netmask), ip2long(ipv4_gateway, 4), str(ipv4_gateway),
               str(ipv6_gateway), int(ipv4_netmask_dec), 1]

        c.execute(
            'INSERT INTO network VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            row)
    else:
        return l
    return


def host(l, c, network_id):
    node_id = node(c)
    c.execute('SELECT vlan FROM network WHERE node_id = ?', (network_id, ))
    vlan = c.fetchone()[0]
    vlan = int(vlan) if not vlan is None else None

    name = l[1]
    ip = l[2]
    if '.' in ip:
        # IPv4
        ipv4_addr = ip
        if vlan:
            last_digits = int(str(ip).split('.')[-1])
            ipv6_addr = "%s:%d::%d" % (_current_v6_base, vlan, last_digits)
        else:
            ipv6_addr = None
    else:
        # IPv6-only
        ipv4_addr = None
        ipv6_addr = ip
        # If it starts with ::, use VLAN if available
        if vlan and ip.startswith('::'):
            ipv6_addr = "%s:%d%s" % (_current_v6_base, vlan, ip)
            print(ipv6_addr)

    row = [
        node_id,
        name,
        ip2long(
            ipv4_addr,
            4) if ipv4_addr else None,
        ipv4_addr,
        ipv6_addr,
        network_id]
    c.execute('INSERT INTO host VALUES (?,?,?,?,?,?)', row)

    options(c, node_id, l[3])

    return


def network(l, c, r):
    node_id = node(c)
    short_name = l[0]
    vlan = int(l[3]) if l[3] != '-' else None
    terminator = l[2]

    # IPv4
    ipv4 = l[1]
    net_ipv4 = ipcalc.Network(ipv4)
    ipv4_gateway = net_ipv4[1]
    ipv4_netmask = str(net_ipv4.netmask())
    ipv4_netmask_dec = int(str(ipv4).split("/")[1])

    # IPv6
    if vlan:
        last_digits = int(str(ipv4_gateway).split('.')[-1])
        ipv6 = "%s:%d::/64" % (_current_v6_base, vlan)
        ipv6_netmask = 64
        ipv6_gateway = "%s:%d::1" % (_current_v6_base, vlan)
    else:
        ipv6 = None
        ipv6_netmask = None
        ipv6_gateway = None

    name = '%s@%s' % (_current_domain, short_name)

    row = [node_id, name, short_name, vlan, terminator, ip2long(ipv4, 4),
           str(ipv4), ipv6, ip2long(ipv4_netmask, 4), str(ipv4_netmask),
           ipv6_netmask, ip2long(ipv4_gateway, 4), str(ipv4_gateway),
           ipv6_gateway, int(ipv4_netmask_dec), 1 if not ipv6 is None else 0]
    c.execute(
        'INSERT INTO network VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        row)

    options(c, node_id, l[4])

    return node_id


def split_value(string):
  """Split a value, but preserve options."""
  split = string.split(',')
  result = []

  level = 0
  buf = []
  for entry in split:
    level += entry.count('(')
    level -= entry.count(')')

    buf.append(entry)
    if level == 0:
      result.append(','.join(buf))
      buf = []
  return result


def options(c, node_id, options):
    for option in options.split(';'):
        option = option.split("=")
        name = option[0]
        if name == '':
            continue
        if len(option) == 2:
            for value in split_value(option[1]):
                row = [node_id, name, value]
                logging.debug('Insert option for %d, %s = %s',
                        node_id, name, value)
                c.execute('INSERT INTO option VALUES(NULL, ?, ?, ?)', row)
        else:
            row = [node_id, name, 1]
            logging.debug('Insert option for %d, %s = 1', node_id, name)
            c.execute('INSERT INTO option VALUES(NULL, ?, ?, ?)', row)


def node(c):
    c.execute('INSERT INTO node VALUES (NULL)')
    c.execute('SELECT last_insert_rowid() as id')
    return int(c.fetchone()[0])


def ip2long(ip, version):
    ip = str(ip).split("/")[0]
    if version == 4:
        packedIP = socket.inet_aton(ip)
        return struct.unpack("!L", packedIP)[0]
    else:
        return int(hexlify(socket.inet_pton(socket.AF_INET6, ip)), 16)


def parser_func(l):
    for exp in SYNTAX:
        if re.match(exp, l[0]):
            return SYNTAX[exp]
    return None


def parse(lines, c):
    network_id = None
    for line in lines:
        if isinstance(line, str):
            line = line.strip().split()
        if len(line) == 0:
            continue
        func = parser_func(line)
        if func:
            parse_using = getattr(MODULE, func, network_id)
            result = parse_using(line, c, network_id)
            network_id = result if result is not None else network_id
