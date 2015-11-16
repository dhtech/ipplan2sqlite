def create(conn):
    c = conn.cursor()

    # Node
    c.execute('''CREATE TABLE node(
    id INTEGER PRIMARY KEY AUTOINCREMENT)''')

    # Hosts
    c.execute('''CREATE TABLE host(
    node_id INTEGER,
    name TEXT,
    ipv4_addr INTEGER,
    ipv4_addr_txt TEXT,
    ipv6_addr_txt TEXT,
    network_id INTEGER,
    FOREIGN KEY (node_id) REFERENCES node (id),
    FOREIGN KEY (network_id) REFERENCES network (id))''')

    # Networks
    c.execute('''CREATE TABLE network(
    node_id INTEGER,
    name TEXT,
    short_name TEXT,
    vlan INTEGER,
    terminator TEXT,
    ipv4 INTEGER,
    ipv4_txt TEXT,
    ipv6_txt TEXT,
    ipv4_netmask INTEGER,
    ipv4_netmask_txt TEXT,
    ipv6_netmask_txt TEXT,
    ipv4_gateway INTEGER,
    ipv4_gateway_txt TEXT,
    ipv6_gateway_txt TEXT,
    ipv4_netmask_dec INTEGER,
    ipv6_capable INTEGER,
    FOREIGN KEY (node_id) REFERENCES node (id))''')

    # Options
    c.execute('''CREATE TABLE option(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER,
    name TEXT,
    value TEXT,
    FOREIGN KEY (node_id) REFERENCES node (id))''')

    # Packages
    c.execute('''CREATE TABLE package(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id INTEGER,
    name TEXT,
    options TEXT,
    FOREIGN KEY (node_id) REFERENCES node (id))''')

    # Services
    c.execute('''CREATE TABLE service(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT,
    dst_ports TEXT,
    src_ports TEXT)''')

    # Flows
    c.execute('''CREATE TABLE flow(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT)''')

    # Firewall rules
    c.execute('''CREATE TABLE firewall_rule(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_node_id INTEGER,
    to_node_id INTEGER,
    service_id INTEGER,
    flow_id INTEGER,
    is_ipv4 BOOLEAN,
    is_ipv6 BOOLEAN,
    FOREIGN KEY (from_node_id) REFERENCES node (id),
    FOREIGN KEY (to_node_id) REFERENCES node (id),
    FOREIGN KEY (service_id) REFERENCES service (id),
    FOREIGN KEY (flow_id) REFERENCES flow (id))''')

    # Table coordinates
    c.execute('''CREATE TABLE  table_coordinates(
    name TEXT,
    hall TEXT,
    x1 INTEGER,
    x2 INTEGER,
    y1 INTEGER,
    y2 INTEGER,
    x_start INTEGER,
    y_start INTEGER,
    width INTEGER,
    height INTEGER,
    horizontal INTEGER)''')

    # Switch coordinates
    c.execute('''CREATE TABLE switch_coordinates(
    name TEXT,
    x INTEGER,
    y INTEGER,
    table_name TEXT)''')

    # Meta data
    c.execute('''CREATE TABLE meta_data(name TEXT, value TEXT)''')

    # Create VIEW node_any
    c.execute('''CREATE VIEW node_any AS
    SELECT node_id, name, ipv4_addr_txt AS ipv4_txt, ipv6_addr_txt AS ipv6_txt
    FROM host UNION SELECT node_id, name, ipv4_txt, ipv6_txt from network''')

    # Create VIEW active_switch
    c.execute('''CREATE VIEW active_switch AS
    SELECT
        n.node_id,
        h.ipv4_addr_txt,
        n.ipv4_txt,
        substr(o.value, 1, 1) AS
            sw, LOWER(n.short_name) ||
            '-' ||
            substr(o.value, 1, 1) ||
            '.event.dreamhack.local'
            AS switch_name
    FROM
        option o,
        network n,
        host h
    WHERE
        h.name = switch_name
        AND o.name = 'sw'
        AND n.node_id = o.node_id
        AND sw <> ''

    UNION

    SELECT
        n.node_id,
        h.ipv4_addr_txt,
        n.ipv4_txt,
        substr(o.value, 2, 1) AS
            sw, LOWER(n.short_name) ||
            '-' ||
            substr(o.value, 2, 1) ||
            '.event.dreamhack.local'
            AS switch_name
    FROM
        option o,
        network n,
        host h
    WHERE
        h.name = switch_name
        AND o.name = 'sw'
        AND n.node_id = o.node_id
        AND sw <> ''

    UNION
    SELECT
        n.node_id,
        h.ipv4_addr_txt,
        n.ipv4_txt,
        substr(o.value, 3, 1) AS
            sw, LOWER(n.short_name) ||
            '-' ||
            substr(o.value, 3, 1) ||
            '.event.dreamhack.local'
            AS switch_name
    FROM
        option o,
        network n,
        host h
    WHERE
        h.name = switch_name
        AND o.name = 'sw'
        AND n.node_id = o.node_id
        AND sw <> '';''')

    # Create VIEW firewall_rule_ip_level
    c.execute('''CREATE VIEW firewall_rule_ip_level AS
    SELECT
        fw.is_ipv4,
        fw.is_ipv6,
        f.name AS from_node_name,
        f.ipv4_txt AS from_ipv4,
        f.ipv6_txt AS from_ipv6,
        t.name AS to_node_name,
        t.ipv4_txt AS to_ipv4,
        t.ipv6_txt AS to_ipv6,
        fl.name AS flow_name,
        s.name AS service_name,
        s.description AS service_description,
        s.dst_ports AS service_dst_ports,
        s.src_ports AS service_src_ports
    FROM
        node_any f,
        node_any t,
        service s,
        firewall_rule fw,
        flow fl
    WHERE
        s.id = fw.service_id
        AND fl.id = fw.flow_id
        AND f.node_id = fw.from_node_id
        AND t.node_id = fw.to_node_id;''')

    conn.commit()
