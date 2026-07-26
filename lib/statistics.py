def gather_all(c):
    c.execute('SELECT COUNT(*) FROM node')
    nbr_of_nodes = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM host')
    nbr_of_hosts = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM network')
    nbr_of_networks = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM firewall_rule')
    nbr_of_firewall_rules = c.fetchone()[0]

    c.execute(
        """SELECT
            COUNT(*)
           FROM
            host h,
            option o
           WHERE h.node_id = o.node_id
           AND o.name = 'tblswmgmt'""")
    nbr_of_switches = c.fetchone()[0]

    c.execute('''SELECT COUNT(*) FROM active_switch;''')
    nbr_of_active_switches = c.fetchone()[0]

    results = {
        "nbr_of_nodes": nbr_of_nodes,
        "nbr_of_hosts": nbr_of_hosts,
        "nbr_of_networks": nbr_of_networks,
        "nbr_of_firewall_rules": nbr_of_firewall_rules,
        "nbr_of_switches": nbr_of_switches,
        "nbr_of_active_switches": nbr_of_active_switches
    }

    return results
