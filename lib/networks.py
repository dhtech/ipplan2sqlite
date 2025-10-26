from __future__ import absolute_import
from builtins import str
import re
from . import ipcalc
import socket
import struct
from binascii import hexlify
from .processor import ip2long, node


def add_all(c):
    add_all_rfc_1918(c)
    add_any(c)


def add_all_rfc_1918(c):
    for ipv4 in ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']:
        vlan = None
        name = "RFC_" + ipv4.split('.')[0]
        short_name = name
        terminator = None
        net_ipv4 = ipcalc.Network(ipv4)
        ipv4_gateway = net_ipv4[1]
        ipv4_netmask = str(net_ipv4.netmask())
        ipv4_netmask_dec = int(str(ipv4).split("/")[1])
        node_id = node(c)

        row = [node_id, name, short_name, vlan, terminator, ip2long(ipv4, 4),
               str(ipv4), None, ip2long(ipv4_netmask, 4), str(ipv4_netmask),
               None, ip2long(ipv4_gateway, 4), str(ipv4_gateway),
               None, int(ipv4_netmask_dec), 0]

        c.execute(
            'INSERT INTO network VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            row)


def add_any(c):
    node_id = node(c)
    vlan = None
    name = "ANY"
    short_name = "ANY"
    terminator = None

    # IPv4
    ipv4 = "0/0"
    ipv4_gateway = None
    ipv4_netmask = None
    ipv4_netmask_dec = None

    # IPv6
    ipv6 = "::/0"
    ipv6_netmask = None
    ipv6_gateway = None

    row = [node_id, name, short_name, vlan, terminator, 0,
           str(ipv4), str(ipv6), None, None, ipv6_netmask,
           ipv4_gateway, ipv4_gateway, ipv6_gateway, ipv4_netmask_dec, 1]

    c.execute(
        'INSERT INTO network VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        row)
