
def get_weighted_neighbors(graph, node, weighted_depth_limit, relationship_filter, label_filter, min_level, max_level):
    '''Takes in a graph and a starting node and goes within a relationship depth limit (by count)
    Returns a list of dictionaries keys=(depth, nodes_at_depth)
    nodes_at_depth is a list of nodes at the corresponding depth
    For more information on the config of spanningTree, see https://neo4j.com/docs/labs/apoc/current/graph-querying/expand-spanning-tree/'''
    
    query_str = """MATCH (n{node_label} {{uuid: '{node_uuid}'}})
                    CALL apoc.path.spanningTree(n, {{relationshipFilter:'{relationship_filter}', labelFilter:'{label_filter}', minLevel:{min_level}, maxLevel:{max_level}}}) YIELD path
                    WITH last(nodes(path)) as node, reduce(weight = 0, rel IN relationships(path) | weight+rel.weight) as depth
                    WHERE depth<{weighted_depth_limit}
                    WITH depth, collect(node) as nodes_at_depth
                    ORDER BY depth ASC
                    RETURN nodes_at_depth, depth""".format(
                node_label=node.labels,
                node_uuid=node['uuid'],
                relationship_filter=relationship_filter,
                label_filter=label_filter,
                min_level=min_level,
                max_level=max_level,
                weighted_depth_limit=weighted_depth_limit
                )

    cursor = graph.run(query_str)
    return cursor


def get_node_context(graph, node):
    '''Takes in a node and return its "context", being all of its part properties type (child) and the block it types a part property of (parent)'''
    query_str = """MATCH (n{node_label} {{name: '{node_name}'}})
                    CALL apoc.path.expand(n, "ATTRIBUTE|TYPED", "", 2,2) YIELD path
                    WITH last(nodes(path)) AS context
                    RETURN context
                        """.format(
                            node_name=node['name'],
                            node_label=node.labels)
    
    cursor = graph.run(query_str)
    return cursor


def get_n_degree_neighbors(graph, node, n):
    '''Takes in a Graph and a node within the graph
    Returns a cursor over the neighbors nodes of degree n only'''

    query_str = "match (r" + str(node.labels) + " {name: '" + node['name'] + "'})-[*" + str(n) + "]-(node) return node"

    cursor = graph.run(query_str)

    return cursor


def get_n_degree_neighbors_label(graph, node, n, neighbor_label, relationship_label=''):
    '''Takes in a Graph and a node within the graph
    Returns a cursor over the neighbors nodes of both degree n and label=label only'''

    query_str = "match (r{node_label} {{name: '{node_name}'}})-[{relationship_label}*{n}]-(node:{neighbor_label}) return node".format(
                    node_label=str(node.labels), 
                    node_name=node['name'],
                    relationship_label=relationship_label,
                    n=str(n), 
                    neighbor_label=neighbor_label
                    )

    cursor = graph.run(query_str)

    return cursor
