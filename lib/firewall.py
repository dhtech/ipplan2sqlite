import collections
import logging
import re


class Service(object):

    def __init__(self, full_name, service_id, flow_id, is_ipv4, is_ipv6):
        self.full_name = full_name
        self.service_id = service_id
        self.flow_id = flow_id
        self.is_ipv4 = is_ipv4
        self.is_ipv6 = is_ipv6

    def __hash__(self):
        # We do not consider ipv4/ipv6 to be qualified to allow
        # easy comparision between services. They shouldn't be stored in the
        # same set.
        return hash((self.full_name, self.service_id, self.flow_id))

    def __eq__(self, other):
        return ((self.full_name, self.service_id, self.flow_id) ==
                (other.full_name, other.service_id, other.flow_id))


def add_services(services, c):
    for service, data in services.iteritems():
        row = [service,
               data.get('description', service),
               ','.join(data['destport']),
               ','.join(data.get('sourceport',[])) or None]
        c.execute('INSERT INTO service VALUES (NULL, ?, ?, ?, ?)', row)


def add_flows(flows, c):
    for flow in flows:
        row = [flow, flow]
        c.execute('INSERT INTO flow VALUES (NULL, ?, ?)', row)


class FirewallGenerator(object):

    def __init__(self, packages, cursor):
        self.packages = packages
        self.c = cursor
        logging.debug('Prefetching nodes')
        self.prefetch_nodes()
        logging.debug('Prefetching nodes:services association')
        self.prefetch_node_and_services()

    def prefetch_nodes(self):
        self.c.execute('SELECT DISTINCT node_id, name FROM package')
        packages = self.c.fetchall()
        self.nodes = collections.defaultdict(set)

        # Convert packages to services
        for node, package in packages:
            self.nodes[node].add(package)

        # Fetch all hosts -> net map
        self.c.execute('SELECT node_id, network_id FROM host')
        self.netmap = {x[0]: x[1] for x in self.c.fetchall()}

    def register_service(self, access, node, service):
        # If we have saved the network node with the same service, skip this
        srv = self.parse_service(node, service)
        self.node_services[access][node].add(srv)

    def prefetch_node_and_services(self):
        access_to_sql_map = {
            'server': 's',
            'client': 'c',
            'world': 'w',
            'local': 'l',
            'public': 'p'
        }

        self.node_services = dict()
        self.service_nodes = dict()
        for access, access_key in access_to_sql_map.iteritems():
            # TODO(bluecmd): These are deprecated in favor of packages
            # We should emit warnings in the presubmit hook to make sure
            # people are not using these
            self.c.execute('SELECT node_id, value FROM option WHERE name = ?', (
                access_key, ))
            explicit = self.c.fetchall()

            self.node_services[access] = collections.defaultdict(set)
            self.service_nodes[access] = collections.defaultdict(set)
            for node, service in explicit:
                self.register_service(access, node, service)

            for node, packset in self.nodes.iteritems():
                for package_name in packset:
                    package = self.packages[package_name] or {}
                    for service in set(package.get(access, [])):
                        self.register_service(access, node, service)

            # Prune redundant flows (hosts that share the network flows)
            for node, services in self.node_services[access].iteritems():
                if node not in self.netmap:
                    continue
                parent = self.node_services[access].get(self.netmap[node])
                if not parent:
                    continue
                self.node_services[access][node] -= parent

            # Construct reverse mapping to help client->server lookups
            for node, srv in self.node_service_iter(access):
                self.service_nodes[access][srv].add((node, srv))

    def node_service_iter(self, access):
        for node, services in self.node_services[access].iteritems():
            for service in services:
                yield (node, service)

    def service_flow_nodes_iter(self, access, service):
        """Returns an iterator for (node_id, service_map)."""
        return self.service_nodes[access].get(service, [])

    def client_server(self):
        # Select all servers
        for server_id, server_srv in self.node_service_iter('server'):
            logging.debug('Generating rules for server %d (%s)',
                    server_id, server_srv.full_name)
            to_node_id = int(server_id)
            clients = self.service_flow_nodes_iter('client', server_srv)
            for client, client_srv in clients:
                # Skip local firewall connections, assume loopback is always
                # allowed
                if client == server_id:
                    continue
                logging.debug('.. to client %d', client)
                from_node_id = int(client)
                row = [from_node_id,
                       to_node_id,
                       client_srv.service_id,
                       client_srv.flow_id,
                       client_srv.is_ipv4 and server_srv.is_ipv4,
                       client_srv.is_ipv6 and server_srv.is_ipv6]
                self.c.execute(
                    'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
                    row)
        return


    def local(self):
        # Select all servers providing services to their VLAN
        for server, service in self.node_service_iter('local'):
            to_node_id = int(server)

            # Which VLAN is this server on?
            self.c.execute(
                'SELECT network_id FROM host WHERE node_id = ?', (to_node_id,))
            from_node_id = int(self.c.fetchone()[0])
            row = [from_node_id,
                   to_node_id,
                   service.service_id,
                   service.flow_id,
                   service.is_ipv4,
                   service.is_ipv6]
            self.c.execute(
                'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
                row)
        return


    def public(self):
        # List public networks
        network_node_ids = {}
        for network in ['EVENT@DREAMHACK', 'RFC_10', 'RFC_172', 'RFC_192']:
            network_node_ids[network] = self.get_network_node_id(network)

        # Select all servers providing services to their VLAN
        for server, service in self.node_service_iter('public'):
            to_node_id = int(server)

            for network in network_node_ids:
                from_node_id = network_node_ids[network]
                row = [from_node_id,
                       to_node_id,
                       service.service_id,
                       service.flow_id,
                       service.is_ipv4,
                       service.is_ipv6]
                self.c.execute(
                    'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
                    row)
        return


    def world(self):
        # Reference for internet
        from_node_id = self.get_network_node_id('ANY')

        # Select all servers providing services to their VLAN
        for server, service in self.node_service_iter('world'):
            to_node_id = int(server)
            row = [from_node_id,
                    to_node_id,
                    service.service_id,
                    service.flow_id,
                    service.is_ipv4,
                    service.is_ipv6]
            self.c.execute(
                'INSERT INTO firewall_rule VALUES (NULL, ?, ?, ?, ?, ?, ?)',
                row)
        return


    def parse_service(self, node_id, service):
        search = re.search('([46]{1,2})$', service)
        service_version = search.group(0) if search else None

        self.c.execute(
                'SELECT node_id FROM network WHERE node_id = ?', (node_id, ))
        is_node_network = bool(self.c.fetchone())

        if is_node_network:
          self.c.execute(
              'SELECT name, node_id FROM network WHERE node_id = ?',
              (node_id, ))
        else:
         self.c.execute(
                'SELECT network.name, network.node_id FROM network, host '
                'WHERE network.node_id = host.network_id AND host.node_id = ?',
                (node_id, ))

        network, network_id = self.c.fetchone()
        domain = network.split('@')[0]

        self.c.execute(
            'SELECT value FROM option WHERE name = "flow" AND node_id = ?',
            (network_id, ))
        res = self.c.fetchone()
        default_flow = res[0] if res else domain.lower()

        is_ipv4 = 0
        is_ipv6 = 0
        if not service_version:
            is_ipv4 = 1
            is_ipv6 = 1
            service_name = service
        else:
            if "4" in service_version:
                is_ipv4 = 1
            if "6" in service_version:
                is_ipv6 = 1
            service_name = service[:-len(service_version)]

        # Flow?
        if "-" in service_name:
            flow_name = service_name.split('-')[0]
            service_name = service_name.split('-', 1)[-1]
            if flow_name == 'default':
                flow_name = default_flow
        else:
            flow_name = default_flow
        flow_id = self.get_flow_id(flow_name)

        # Service?
        service_id = self.get_service_id(service_name)
        if service_id is None:
          raise Exception(
              "Internal Error: Failed to map service %s -> ID" % service_name)

        return Service(service, service_id, flow_id, is_ipv4, is_ipv6)


    def get_flow_id(self, flow_name):
        self.c.execute('SELECT id FROM flow WHERE name = ?', (flow_name, ))
        return next(iter(self.c.fetchone() or ()), None)


    def get_service_id(self, service_name):
        self.c.execute(
                'SELECT id FROM service WHERE name = ?', (service_name, ))
        return next(iter(self.c.fetchone() or ()), None)


    def get_network_node_id(self, network_name):
        self.c.execute(
                'SELECT node_id FROM network WHERE name = ?', (network_name,))
        return next(iter(self.c.fetchone() or ()), None)


def build(packages, c):
    f = FirewallGenerator(packages, c)
    logging.debug('Generating client:server rules')
    f.client_server()
    logging.debug('Generating local rules')
    f.local()
    logging.debug('Generating public rules')
    f.public()
    logging.debug('Generating world rules')
    f.world()
