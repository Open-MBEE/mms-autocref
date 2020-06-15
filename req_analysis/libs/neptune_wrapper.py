from gremlin_python.process.graph_traversal import __, both, hasLabel, hasId, out
import signal
from contextlib import contextmanager

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)



def node_distance(neptune_instance, el_1, el_2):
    '''Returns the number of hops in the shortest path between 2 elements'''
    try:
        with time_limit(3):
            path = neptune_instance.V(el_1).repeat(both().not_(hasId('master')).simplePath()).until(hasId(el_2).or_().loops().is_(8)).path().limit(1).toList()[0]
            if (path[0].id == el_1) and (path[-1].id == el_2):
                return len(path)-1
            else:
                return 10
    except TimeoutException as e:
        print("Timeout")
        return 10


def get_node_neighbors(neptune_instance, node):
    '''Returns the one-degree neighbors of a node'''

    return neptune_instance.V(node).both().toList()


def get_common_owner(neptune_instance, el_1, el_2):
    '''Returns the lowest common ancestor in the containment tree of the model
    see: http://tinkerpop.apache.org/docs/current/recipes/#_lowest_common_ancestor'''

    return neptune_instance.V(el_1).repeat(out('ownerElement')).emit().as_('x').repeat(__.in_('ownerElement')).emit(hasId(el_2)).select('x').limit(1).toList()


def get_type_from_part_properties(neptune_instance, node):
    '''Returns the list of vertices that are the Type (Class) of a part property from node'''

    return neptune_instance.V(node).out('ownedAttributeFromClass').hasLabel('Property').out('typeFromTypedElement').hasLabel('Class').toList()


def get_owner(neptune_instance, el_1):
    '''Returns the lowest common ancestor in the containment tree of the model
    see: http://tinkerpop.apache.org/docs/current/recipes/#_lowest_common_ancestor'''

    return neptune_instance.V(el_1).out('ownerElement').limit(1).toList()


def get_named_classes(neptune_instance):
    return neptune_instance.V().hasLabel('Class').has('_label').toList()
