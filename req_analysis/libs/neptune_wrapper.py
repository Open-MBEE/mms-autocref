from gremlin_python.process.graph_traversal import __, both, hasLabel, hasId


def node_distance(neptune_instance, el_1, el_2):
    return len(neptune_instance.V(el_1).repeat(both().not_(hasId('master')).simplePath()).until(hasId(el_2).or_().loops().is_(8)).path().limit(1).toList()[0])
