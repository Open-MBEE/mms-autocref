from SPARQLWrapper import SPARQLWrapper, JSON, POST
from req_analysis.requirement import Requirement
import time
import networkx as nx

class Model():

    def __init__(self, sparql_url):
        self.sparql = SPARQLWrapper(sparql_url)


    def clear_graph(self, graph_url):
        '''Clears the SPARQL graph of URL graph_url
        This is intended to clear the output graph of all prior analyses'''

        self.sparql.setMethod(POST)
        self.sparql.setQuery("clear graph " + graph_url)

        return self.sparql.query()

    
    def get_model_elements(self, query_str):
        '''Returns a dict (Keys = {uri, name}) of all model elements within the SPARQL Graph'''
        self.sparql.setQuery(query_str)
        self.sparql.setReturnFormat(JSON)

        results = self.sparql.query().convert()
        model_elements = []

        for result in results["results"]["bindings"]:
            model_elements.append(dict(uri=result['element']['value'], name=result['label']['value']))

        self.model_elements = model_elements
        return model_elements


    def get_requirement_by_id(self, value_name, element_id):
        '''Returns a SINGLE requirement element based on its ID'''
        self.sparql.setQuery(SINGLE_TEXT_ELEMENT_QUERY_STR.format(value_name=value_name, element_id=element_id))
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()

        return results["results"]["bindings"]


    def get_text_elements(self, query_str):
        '''Runs query_str and returns the results'''
        self.sparql.setQuery(query_str)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()

        return results["results"]["bindings"]


    def match_requirement(self, neptune_graph, requirement_dict, model_elements, pprint=False):
        time1 = time.time()

        req_object = Requirement(requirement_dict["instance"]["value"], requirement_dict["valueString"]["value"])
        matches, count = req_object.match_req_tokens(model_elements, 0.0035)

        if pprint:
            print('Req ID: ', requirement_dict["instance"]["value"], '\nReq text:' , requirement_dict["valueString"]["value"], '\n__________')
            print(matches, '\n___________')
            print(count, 'comparaisons')
            print('Time: ', time.time()-time1)

        req_object.init_match_subgraph(neptune_graph)  

        if pprint:
            pos = nx.circular_layout(req_object.req_subgraph)
            nx.draw_networkx_edge_labels(req_object.req_subgraph, pos)
            nx.draw_circular(req_object.req_subgraph, with_labels=True)      
        

        definitive_matches = req_object.match_clustering()

        if pprint:
            for match in definitive_matches.values():
                print('Token: ', match['token']['text'])
                print('Element: ', match['model_element']['name'])
                print('URI: ', match['model_element']['uri'], '\n_________')

        allocations = req_object.allocation_discovery(neptune_graph)

        if pprint:
            for alloc in allocations.values():
                print('Token: ', alloc['token']['text'])
                print('Element: ', alloc['model_element']['name'])
                print('URI: ', alloc['model_element']['uri'], '\n_________')

        return None



SINGLE_TEXT_ELEMENT_QUERY_STR = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
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
select * from mms-graph:data.tmt {{
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

    values ?{value_name} {{ mms-element:{element_id} }}
}}
"""