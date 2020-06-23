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


    def init_requirement_elements(self):
        '''Runs Class attribute QUERY_REQUIREMENTS and returns the results'''
        self.sparql_wrapper.setQuery(QUERY_REQUIREMENTS)
        self.sparql_wrapper.setReturnFormat(JSON)

        results = self.sparql_wrapper.query()

        for result in results.convert()["results"]["bindings"]:
            self.requirements[result['slotValue']['value'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', '')] = result

        print('== Status Code:', results.response.code, '==')
        print(len(self.requirements), 'requirements found.')


    def get_requirement_by_id(self, element_id):
        '''Returns a SINGLE requirement element based on its ID'''
        
        return self.requirements[element_id]


    def evaluate_req_by_id(self, neptune_graph, requirement_id, reference_targets, pprint=False):
        '''Runs an Evaluation flow on a requirement, matched against reference_targets
        pprint=True will output the analysis real time'''

        time1 = time.time()

        requirement_dict = self.get_requirement_by_id(requirement_id)
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

    def evaluate_all_requirements(self, neptune_graph, reference_targets, insert_blocks, insert_query):
        '''Runs an Evalution flow for all requirements in the requirement_evaluator
        THIS WILL TAKE A (VERY) LONG TIME'''

        c, max_evals = 0, len(self.requirements.keys())
        for req_id in self.requirements.keys():
            c += 1
            try:
                req_evaluation = self.evaluate_req_by_id(neptune_graph, 
                                                req_id, 
                                                reference_targets,
                                                pprint=False)
                req_evaluation.insert_references(insert_blocks, insert_query)
                print(c, '/', max_evals, '--- EVALUATION done for req: ', req_id)
            except ValueError:
                print(c, '/', max_evals, '--- NO MATCH FOUND evaluation with req: ', req_id)
            except:
                print(c, '/', max_evals, '--- FAILED evaluation with req: ', req_id)


QUERY_REQUIREMENTS = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix xml: <http://www.w3.org/XML/1998/namespace/>
prefix mms-ontology: <https://opencae.jpl.nasa.gov/mms/rdf/ontology/>
prefix mms-graph: <https://opencae.jpl.nasa.gov/mms/rdf/graph/>
prefix mms-property: <https://opencae.jpl.nasa.gov/mms/rdf/property/>
prefix mms-class: <https://opencae.jpl.nasa.gov/mms/rdf/class/>
prefix mms-element: <https://opencae.jpl.nasa.gov/mms/rdf/element/>
prefix mms-artifact: <https://opencae.jpl.nasa.gov/mms/rdf/artifact/>
prefix mms-index: <https://opencae.jpl.nasa.gov/mms/rdf/index/>
prefix xmi: <http://www.omg.org/spec/XMI/20131001#>
prefix uml: <http://www.omg.org/spec/UML/20161101#>
prefix uml-model: <https://www.omg.org/spec/UML/20161101/UML.xmi#>
prefix uml-primitives: <https://www.omg.org/spec/UML/20161101/PrimitiveTypes.xmi#>
prefix uml-class: <https://opencae.jpl.nasa.gov/mms/rdf/uml-class/>
prefix uml-property: <https://opencae.jpl.nasa.gov/mms/rdf/uml-property/>

# `Class` that has an `appliedStereotypeInstance` `InstanceSpecification` whose type is <<Requirement>> Stereotype (ID)
select * from mms-graph:data.tmt {
    # `Class` that has an `appliedStereotypeInstance`...
    ?class a uml-class:Class ;
        mms-property:appliedStereotypeInstance ?instance ;
        .

    # `InstanceSpecification`. Stereotype classifier and all slots
    ?instance mms-property:slot ?slot ;
        .

    # Slot --> value
    ?slot mms-property:valueValueSpecificationFromSlot ?slotValue ;
        .

    # value --> string
    ?slotValue a uml-class:LiteralString ;
        mms-property:valueString ?valueString ;
        .

    # filter string by those starting with html
    filter(regex(?valueString, \"^\\\\s*<\"))
}
"""