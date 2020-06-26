import spacy
import networkx as nx
import numpy as np
import uuid

from req_analysis.sparql import INSERT_BLOCKS, INSERT_QUERY
from req_analysis.libs.metrics import fuzzy_match_score, remove_stopwords_from_string
from req_analysis.libs.neptune_wrapper import node_distance, get_node_neighbors

import scipy
import scipy.spatial.distance as ssd
import scipy.cluster.hierarchy as hrchy

import time

import en_core_web_sm
nlp_np = en_core_web_sm.load()
merge_nps = nlp_np.create_pipe("merge_noun_chunks")
nlp_np.add_pipe(merge_nps)



class Evaluation():


    def __init__(self, uri, text, reference_targets, sparql_wrapper):
        self.sparql_wrapper = sparql_wrapper
        self.model_elements = reference_targets.table
        self.uri = uri
        self.mms_id = uri.replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', '')
        self.evaluation_uuid = uuid.uuid4().hex
        self.text = text
        self.tokens = []
        self.transclusion_relations = []

        for token in nlp_np(self.text):
            self.tokens.append(dict(text=token.text, pos=token.pos_, token_id=token.i, whitespace=token.whitespace_))

        self.matches_subgraph = None   # Initialized by self.init_match_subgraph()
        self.winners = None        # Initialized by self.match_clustering()
        self.allocations = None     # Initialized by self.allocation_discovery()
        self.cref_text = None



    def get_matches(self):
        return self.winners

    def get_allocations(self):
        return self.allocations

    def display_match_subgraph(self):
        '''Displays the NetworkX subgraph of the found matches'''
        pos = nx.circular_layout(self.matches_subgraph)
        nx.draw_networkx_edge_labels(self.matches_subgraph, pos)
        nx.draw_circular(self.matches_subgraph, with_labels=True)


    def evaluate(self, neptune_graph, remove_stopwords=False, pprint=False):
        '''Runs a whole evaluation, from match_tokens() to allocation_discovery()'''
        
        time1 = time.time()
        matches, count = self.match_tokens(0.0035, remove_stopwords=remove_stopwords)

        if pprint:
            print(matches, '\n___________')
            print(count, 'comparaisons')
            print('Time: ', time.time()-time1)

        self.init_match_subgraph(neptune_graph, pprint)  

        if pprint:
            pos = nx.circular_layout(self.matches_subgraph)
            nx.draw_networkx_edge_labels(self.matches_subgraph, pos)
            nx.draw_circular(self.matches_subgraph, with_labels=True)
        

        definitive_matches = self.match_clustering()

        if pprint:
            print('_______________________\nMATCHES:')
            for match in definitive_matches.values():
                print('Token: ', match['token']['text'])
                print('Element: ', match['model_element']['name'])
                print('URI: ', match['model_element']['uri'], '\n_________')


        allocations = self.allocation_discovery(neptune_graph)

        if pprint:
            print('_______________________\nALLOCATIONS:')
            for alloc in allocations:
                print('-', alloc)



    def match_tokens(self, match_threshold, remove_stopwords=False, pos_list=["NOUN", "PROPN"]):
        '''Returns a list of matches between the tokens in the text and the list of model_elements
        Will match on the 'name' attribute of the model_elements dictionnaries'''

        self.transclusion_relations.clear()
        count=0
        # In all tokens
        for token in self.tokens:
            # Only POS of interest
            if token['pos'] in pos_list:

                found_match = None
                if remove_stopwords:
                    token_compare = remove_stopwords_from_string(token['text'])
                else:
                    token_compare = token['text']

                for element in self.model_elements:
                    count+=1
                    fuzzy_score = fuzzy_match_score(token_compare, element['name'])

                    if fuzzy_score < match_threshold:

                        found_match = dict(token=token, model_element=element, score=fuzzy_score)
                        self.transclusion_relations.append(found_match)

        return self.transclusion_relations, count


    def init_match_subgraph(self, g, pprint=False):
        '''Initializes a NetworkX subgraph that contains all the couple (token, model_element_match) found and their edges are
        weighted on their distance in the model'''
        number_matches = len(self.transclusion_relations)
        matches_subgraph = nx.Graph()

        # We want one node per matched token and not per model element matched
        # The more it is referenced, the more important it is (if the text says 'APS' 10 times, APS has to be important)
        for i in range(number_matches):
            matches_subgraph.add_node(i, **self.transclusion_relations[i])

        for i in range(number_matches):
            for j in range(i+1, number_matches):
                el_i, el_j = self.transclusion_relations[i]['model_element'], self.transclusion_relations[j]['model_element']

                if el_i == el_j:

                    dist_ij = 0.1
                    if pprint: print(i, j)
                    if pprint: print('The 2 model elements are the same')

                else:
                    if pprint: print(i, j)
                    # if pprint: print(el_i, el_j)
                    time1 = time.time()
                    try:
                        dist_ij = node_distance(g, el_i['mms_id'], el_j['mms_id'], pprint)
                        if pprint: print('DISTANCE: in', time.time()-time1, 's ', dist_ij)
                    except:
                        dist_ij = 11
                        if pprint: print('FAILURE in ', time.time()-time1, 's:  ', dist_ij)
                    if pprint: print('_________')

                matches_subgraph.add_edge(i, j, weight=dist_ij)

        self.matches_subgraph = matches_subgraph
        return matches_subgraph


    def match_clustering(self):
        '''Uses the NetworkX matches_subgraph and Scipy's linkage matrix to order the subgraph by
        hierarchical clustering order, and returns the correct matches'''

        k = 1
        max_k = self.matches_subgraph.number_of_nodes()
        winners=dict()

        # if there is 0 or 1 match, no disambiguation needed and we can return the unique match (or none)
        if max_k==0 or max_k==1:
            self.winners = {match['token']['token_id']: match for match in self.transclusion_relations}
            return self.winners

        cluster = order_clustering(self.matches_subgraph, max_k)

        for el_i in cluster:
            token_i_id = self.matches_subgraph.nodes(data=True)[el_i]['token']['token_id']
            if token_i_id not in winners:
                winners[token_i_id]=self.matches_subgraph.nodes(data=True)[el_i]

        self.winners = winners
        return winners


    def allocation_discovery(self, g):
        '''Discover allocations based on distance between the winners'''

        allocation_candidate = [candidate['model_element'] for candidate in self.winners.values()]
        allocation_ids = [candidate['mms_id'] for candidate in allocation_candidate]

        for candidate in allocation_candidate:

            candidate_neighbors = get_node_neighbors(g, candidate['mms_id'])

            for neighbor in candidate_neighbors:

                if neighbor.id in allocation_ids: 
                    # Maybe we want more tuning there, to chose if we pop the neighbor or the candidate
                    # TODO: Score based on how many neighbors you have, etc.. 

                    allocation_candidate.pop(neighbor)

        self.allocations = allocation_candidate
        return allocation_candidate


    def init_cref_tags_text(self):
        '''Inserts the <cref id=...> tags in the text, in the Evaluation.cref_text attribute'''
        
        cref_text = ''
        
        for token in self.tokens:
            
            if token['token_id'] in self.get_matches():
                match_id = self.get_matches()[token['token_id']]['model_element']['mms_id']
                cref_text = cref_text + '<cref id="' + match_id + '">' + token['text'] + '</cref>' + token['whitespace']

            else:
                cref_text = cref_text + token['text'] + token['whitespace']

        self.cref_text = cref_text
        return cref_text


    def insert_references(self):
        '''Inserts back the found references (winner) into the SPARQL graph'''
        insert_concat = """"""

        for winner in self.winners.values():
            insert_concat += INSERT_BLOCKS.format(input_uri = self.uri,
                                        input_text = self.text.replace('"', r'\"'),
                                        output_text = self.cref_text.replace('"', r'\"'),
                                        evaluation_uuid = self.evaluation_uuid,
                                        reference_uuid = uuid.uuid4().hex,
                                        match_uri = winner['model_element']['uri'],
                                        token_position = winner['token']['token_id'],
                                        token_text = winner['token']['text'].replace('"', r'\"'))

        insert_str = INSERT_QUERY.format(insert_blocks=insert_concat)

        self.sparql_wrapper.setMethod("POST")
        self.sparql_wrapper.setQuery(insert_str)


        results = self.sparql_wrapper.query()
        return results.response.read()


    def insert_allocations(self):
        '''Inserts the allocations into the SPARQL graph'''
        #TODO
        pass


# Clusters all the way and returns an ordonated list
def order_clustering(G, k):
    '''Utility function used to execute a hierarchical clustering
    The first element of the list of each cluster is its age'''
    D = hrchy.linkage(ssd.squareform(nx.to_numpy_matrix(G)))
    n = np.shape(D)[0] + 1
    k = min(k,n - 1)
    cluster = {i:[0, i] for i in range(n)}
    for t in range(k):
        C1, C2 = cluster.pop(int(D[t][0])), cluster.pop(int(D[t][1]))
        if len(C1) > len(C2):
            cluster[n + t] = [t+1] + C1[1:] + C2[1:]
        elif len(C1) < len(C2):
            cluster[n + t] = [t+1] + C2[1:] + C1[1:]
        else:
            if C1[0] < C2[0]:
                cluster[n + t] = [t+1] + C1[1:] + C2[1:]
            elif C1[0] > C2[0]:
                cluster[n + t] = [t+1] + C2[1:] + C1[1:]
            else:
                if C1[0]!=0 or C2[0]!=0:
                    print('WARNING: Same age but not equal to 0')
                elif G.nodes(data=True)[C1[1]]['token']['token_id'] == G.nodes(data=True)[C2[1]]['token']['token_id']:
                    print('WARNING: Same age (0) and same token were merged', G.nodes(data=True)[C1[1]]['token'])
                    cluster[n + t] = [t+1] + C1[1:] + C2[1:]
                else:
                    cluster[n + t] = [t+1] + C1[1:] + C2[1:]

    return cluster[n+t][1:]