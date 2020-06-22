from SPARQLWrapper import JSON, POST

class ReferenceTarget():

    def __init__(self, sparql_wrapper):
        self.sparql_wrapper = sparql_wrapper
        self.table = [] # initialized with self.init_table()


    
    def init_table(self, query_str):
        '''Accepts a query_str and queries for all model elements
        Initializes table attribute as a list of dict (Keys = {uri, name})
        Returns response info'''
        self.sparql_wrapper.setQuery(query_str)
        self.sparql_wrapper.setReturnFormat(JSON)

        response_ = self.sparql_wrapper.query()
        results = response_.convert()

        for result in results["results"]["bindings"]:
            self.table.append(dict(uri=result['element']['value'], name=result['label']['value']))

        print('== Status Code:', response_.response.code, '==')
        print(len(self.table), 'reference targets found.')
