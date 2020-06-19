from SPARQLWrapper import SPARQLWrapper, JSON, POST
from req_analysis.evaluation import Evaluation
import time
import networkx as nx

class RequirementEvaluator():

    def __init__(self, sparql_wrapper):
        self.sparql_wrapper = sparql_wrapper
        self.requirements = dict() # initialized with self.init_requirement_elements()


    def clear_graph(self, graph_url):
        '''Clears the SPARQL graph of URL graph_url
        This is intended to clear the output graph of all prior analyses'''

        self.sparql_wrapper.setMethod(POST)
        self.sparql_wrapper.setQuery("clear graph " + graph_url)

        return self.sparql_wrapper.query()


    def init_requirement_elements(self, query_str):
        '''Runs query_str and returns the results'''
        self.sparql_wrapper.setQuery(query_str)
        self.sparql_wrapper.setReturnFormat(JSON)

        results = self.sparql_wrapper.query()

        for result in results.convert()["results"]["bindings"]:
            self.requirements[result['slotValue']['value'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', '')] = result

        print('Status Code:', results.response.code)
        print(len(self.requirements), 'requirements found.')


    def get_requirement_by_id(self, element_id):
        '''Returns a SINGLE requirement element based on its ID'''
        
        return self.requirements[element_id]


    def evaluate_req_by_id(self, neptune_graph, element_id, reference_targets, pprint=False):

        time1 = time.time()

        requirement_dict = self.get_requirement_by_id(element_id)
        model_elements = reference_targets.table

        req_evaluation = Evaluation(requirement_dict["instance"]["value"], requirement_dict["valueString"]["value"], self.sparql_wrapper)
        matches, count = req_evaluation.match_tokens(model_elements, 0.0035)

        if pprint:
            print('Req ID: ', requirement_dict["instance"]["value"], '\nReq text:' , requirement_dict["valueString"]["value"], '\n__________')
            print(matches, '\n___________')
            print(count, 'comparaisons')
            print('Time: ', time.time()-time1)

        req_evaluation.init_match_subgraph(neptune_graph, pprint)  

        if pprint:
            pos = nx.circular_layout(req_evaluation.matches_subgraph)
            nx.draw_networkx_edge_labels(req_evaluation.matches_subgraph, pos)
            nx.draw_circular(req_evaluation.matches_subgraph, with_labels=True)
        

        definitive_matches = req_evaluation.match_clustering()

        if pprint:
            print('_______________________\nMATCHES:')
            for match in definitive_matches.values():
                print('Token: ', match['token']['text'])
                print('Element: ', match['model_element']['name'])
                print('URI: ', match['model_element']['uri'], '\n_________')


        allocations = req_evaluation.allocation_discovery(neptune_graph)

        if pprint:
            print('_______________________\nALLOCATIONS:')
            for alloc in allocations.values():
                print('Token: ', alloc['token']['text'])
                print('Element: ', alloc['model_element']['name'])
                print('URI: ', alloc['model_element']['uri'], '\n_________')

        return req_evaluation


