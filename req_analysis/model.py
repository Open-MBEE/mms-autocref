from py2neo import Relationship

from req_analysis.context_cluster import ContextCluster
from req_analysis.requirement import Requirement



class Model():
    def __init__(self, graph, match_threshold):
        self.graph = graph
        self.match_threshold = match_threshold
        self.contexts = [ContextCluster(cursor['n']) for cursor in graph.run("match (n:Block) return n")]


    def get_qualified_name(self, node):
        '''Returns the fully qualified name (root::Folder_name....) of the node'''
        qualified_name = "root"
        query = "match path=shortestPath((root:Folder {{name: 'root'}})-[*1..20]->(b{0} {{name: '{1}'}})) return nodes(path)".format(node.labels, node['name'])
        for node in self.graph.run(query).evaluate()[1:]:
            qualified_name += "::" + node['name']
        return qualified_name


    def create_req_object(self, req_node):
        '''Takes in a requirement in the Model and creates a Requirement instance'''
        return Requirement(self, req_node)



    def append_req_graph(self, req_object):
        '''Appends to the Model a ReqPhrase node and its ReqChunk children based on req_object'''
        if req_object.phrase_node == None:
            raise ValueError('Requirement nodes need to be initialized with req.init_req_nodes()')
        self.graph.create(req_object.phrase_node)
        self.graph.create(req_object.phrase_relation)

        for token_node in req_object.token_nodes:
            self.graph.create(token_node)
        for token_relation in req_object.token_relations: 
            self.graph.create(token_relation)



    def link_matches(self, match_list):
        '''Takes in a match list and creates the corresponding edges in the graph'''
        for match in match_list:
            self.graph.create(Relationship(match['token_node'], "REFERENCES", match['neighbor_node']))
