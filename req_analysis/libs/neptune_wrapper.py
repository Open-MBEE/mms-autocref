from gremlin_python.process.graph_traversal import __, both, hasLabel, hasId
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
    