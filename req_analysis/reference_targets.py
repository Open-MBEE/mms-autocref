from SPARQLWrapper import JSON, POST
from req_analysis.sparql import QUERY_ELEMENTS

class ReferenceTargets():

    def __init__(self, sparql_wrapper):
        self.sparql_wrapper = sparql_wrapper
        self.table = [] # initialized with self.init_table()


    
    def init_table(self):
        '''Queries for all model elements
        Initializes table attribute as a list of dict (Keys = {uri, name})
        Returns response info'''
        self.sparql_wrapper.setQuery(QUERY_ELEMENTS)
        self.sparql_wrapper.setReturnFormat(JSON)

        response_ = self.sparql_wrapper.query()
        results = response_.convert()

        for result in results["results"]["bindings"]:
            self.table.append(dict(uri=result['element']['value'],
                                   name=result['label']['value'],
                                   mms_id=result['element']['value'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', '')))

        print('== Status Code:', response_.response.code, '==')
        print(len(self.table), 'reference targets found.')
