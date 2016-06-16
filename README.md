[![Build Status](https://travis-ci.org/dhtech/ipplan2sqlite.svg)](https://travis-ci.org/dhtech/ipplan2sqlite)
[![Coverage Status](https://coveralls.io/repos/dhtech/ipplan2sqlite/badge.svg)](https://coveralls.io/r/dhtech/ipplan2sqlite)

ipplan2sqlite
=============

Because plain text is awesome, but sometimes cumbersome.

Used by the Dreamhack Network Crew.

## Example file

The file needs to use tabs for alignment, size 8 is recommended. UTF8 and UNIX line feed are required.

    #Name             #Terminator   #Net              #VLAN     #Options
    DHTECH-TEST-1     R1            77.80.255.192/26  303       pkg=opsagent;flow=colo
    #GW                             77.80.255.193
    #$ test.event.dreamhack.se      77.80.255.196               pkg=something
   
    #Name             #Terminator   #Net              #VLAN     #Options
    DHTECH-TEST-2     R1            10.20.4.0/24      204       nat=1.2.3.4
    #GW                             10.20.4.1
    #$ host.tech.dreamhack.local    10.20.4.3                   os=esxi

## How to define a network

Each row in the file is either a comment (line starting with #) or a definition of a network. A network definition must always have 5 space-separated columns (many scripts depend on this).

Example:

    C01                     D-ASR-V         77.80.128.0/25          301             dhcp;resv=20;sw=abc;int=Te0/2/0/1

`C01` is the name of the network, this is an table in hall C, table 1.

`D-ASR-V` is the Layer 3 terminator of the network, the default gateway.

`77.80.128.0/25` is the network with the netmask in CIDR.

`301` is the VLANID, all networks have an VLANID in case that is needed, otherwise use `-`. The IPv6 networks are calculated from the VLANID.

The last column defines special options for the network. The format is `option1=value1,value2,value3;option2=value4` and so on.
If you dont have any options use `none`.

## How to define a host

Example:

    #$ deploy.event.dreamhack.se    77.80.231.70    s=ssh64;c=ldap64,log64;l=tftp64,dhcp64

`#$` is used to indicate that this is a host row.

`deploy.event.dreamhack.se` is the FQDN for the host.

`77.80.231.70` is the IPv4 address of the host. IPv6 is generated from this and the network's VLAN ID.

The last column defines special options for the host. The format is `option1=value1,value2,value3;option2=value4` and so on.
If you dont have any options use `none`.

## Networks comments

All public networks that are free for use shall be commented with: "#-FREE- <network>"

Example:

    #-FREE-                                 77.80.166.128/25

All RFC1918 networks that are free for use shall be commented with: "#-FREE-RFC1918 <network>"

Example:

    #-FREE-RFC1918                                  10.32.8.0/24
