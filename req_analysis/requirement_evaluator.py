from SPARQLWrapper import SPARQLWrapper, JSON, POST
from req_analysis.evaluation import Evaluation
from req_analysis.sparql import QUERY_REQUIREMENTS
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


    def init_requirement_elements(self):
        '''Runs a SPARQL query to get the requirements of the model
        Returns them in a dictionnary, with key=req_id'''
        self.sparql_wrapper.setQuery(QUERY_REQUIREMENTS)
        self.sparql_wrapper.setReturnFormat(JSON)

        results = self.sparql_wrapper.query()

        for result in results.convert()["results"]["bindings"]:
            self.requirements[result['instance']['value'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', '')] = result

        print('== Status Code:', results.response.code, '==')
        print(len(self.requirements), 'requirements found.')


    def get_requirement_by_id(self, element_id):
        '''Returns a SINGLE requirement element based on its ID'''
        
        return self.requirements[element_id]


    def get_evaluation_by_id(self, requirement_id, reference_targets):
        '''Returns the Evaluation object for requiremenet_id
        The only purpose of this function is for an in-depth demo/walkthrough'''
        requirement_dict = self.get_requirement_by_id(requirement_id)

        req_evaluation = Evaluation(requirement_dict["instance"]["value"], requirement_dict["valueString"]["value"], reference_targets, self.sparql_wrapper)

        return req_evaluation


    def evaluate_req_by_id(self, neptune_graph, requirement_id, reference_targets, remove_stopwords=False, pprint=False):
        '''Runs an Evaluation flow on a requirement, matched against reference_targets
        pprint=True will output the analysis real time'''

        requirement_dict = self.get_requirement_by_id(requirement_id)
        model_elements = reference_targets.table

        req_evaluation = Evaluation(requirement_dict["instance"]["value"], requirement_dict["valueString"]["value"], reference_targets, self.sparql_wrapper)
        
        req_evaluation.evaluate(neptune_graph, remove_stopwords=remove_stopwords, pprint=pprint)

        return req_evaluation

    def evaluate_all_requirements(self, neptune_graph, reference_targets, max_evals=0, pprint=False):
        '''Runs an Evalution flow for all requirements in the requirement_evaluator
        THIS WILL TAKE A (VERY) LONG TIME'''

        c, req_total = 0, len(self.requirements.keys())
        time2 = time.time()
        for req_id in self.requirements.keys():
            c += 1
            try:
                req_evaluation = self.evaluate_req_by_id(neptune_graph, 
                                                req_id, 
                                                reference_targets,
                                                pprint=pprint)
                req_evaluation.insert_references()
                print(c, '/', req_total, '---', time.time()-time2, 's\nEVALUATION done for req: ', req_id)
            except ValueError:
                print(c, '/', req_total, '---', time.time()-time2, 's\nNO MATCH FOUND evaluation with req: ', req_id)
            except:
                print(c, '/', req_total, '---', time.time()-time2, 's\nFAILED evaluation with req: ', req_id)
            
            if c==max_evals: 
                break


