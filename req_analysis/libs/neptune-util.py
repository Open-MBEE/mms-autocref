from __future__ import print_function
from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.anonymous_traversal import *
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import *
from tornado.httpclient import HTTPError

import os
import json
import urllib.request
import time
import warnings
import sys

class Neptune:
    def remoteConnection(self, neptune_endpoint=None, neptune_port=None, show_endpoint=True):
        neptune_gremlin_endpoint = self.gremlin_endpoint(neptune_endpoint, neptune_port)
        if show_endpoint:
            print('gremlin: ' + neptune_gremlin_endpoint)
        retry_count = 0
        while True:
            try:
                return DriverRemoteConnection(neptune_gremlin_endpoint,'g')
            except HTTPError as e:
                exc_info = sys.exc_info()
                if retry_count < 3:
                    retry_count+=1
                    print('Connection timeout. Retrying...')
                else:
                    raise exc_info[0].with_traceback(exc_info[1], exc_info[2])
    
    def graphTraversal(self, neptune_endpoint=None, neptune_port=None, show_endpoint=True, connection=None):
        if connection is None:
            connection = self.remoteConnection(neptune_endpoint, neptune_port, show_endpoint)
        return traversal().withRemote(connection)
    
    def __wait(self, status_url, interval):
        while True:
            status, jsonresponse = self.bulkLoadStatus(status_url)
            if status == 'LOAD_COMPLETED':
                print('load completed')
                break
            if status == 'LOAD_IN_PROGRESS':
                print('loading... {} records inserted'.format(jsonresponse['payload']['overallStatus']['totalRecords']))
                time.sleep(interval)
            else:
                raise Exception(jsonresponse)

    def gremlin_endpoint(self, neptune_endpoint=None, neptune_port=None):
        return self.__endpoint('ws', self.__neptune_endpoint(neptune_endpoint), self.__neptune_port(neptune_port), 'gremlin')
    
    def __endpoint(self, protocol, neptune_endpoint, neptune_port, suffix):
        return '{}://{}:{}/{}'.format(protocol, neptune_endpoint, neptune_port, suffix)
    
    def __neptune_endpoint(self, neptune_endpoint=None):
        if neptune_endpoint is None:
            neptune_endpoint = os.environ['NEPTUNE_CLUSTER_ENDPOINT']
        return neptune_endpoint
    
    def __neptune_port(self, neptune_port=None):
        if neptune_port is None:
            neptune_port = os.environ['NEPTUNE_CLUSTER_PORT']
        return neptune_port
    
statics.load_statics(globals())

del globals()['range']
del globals()['map']

neptune = Neptune()
