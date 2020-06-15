from req_analysis.libs.neo4j_wrapper import get_node_context

class ContextCluster():

    
    def __init__(self, source_node):
        self.source_node = source_node
        self.context = [neighbor['context'] for neighbor in get_node_context(self.source_node.graph, self.source_node)]




    def get_context(self):
        return self.context
    

    