import spacy
import networkx as nx
import numpy as np
import uuid

from req_analysis.sparql import INSERT_BLOCKS, INSERT_QUERY
from req_analysis.libs.metrics import fuzzy_match_score
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


    def __init__(self, uri, text, sparql_wrapper):
        self.sparql_wrapper = sparql_wrapper
        self.uri = uri
        self.text = text
        self.tokens = []
        self.transclusion_relations = []

        for token in nlp_np(self.text):
            self.tokens.append(dict(text=token.text, pos=token.pos_, token_id=token.i))

        self.matches_subgraph = None   # Initialized by self.init_match_subgraph()
        self.winners = None        # Initialized by self.match_clustering()
        self.allocations = None     # Initialized by self.allocation_discovery()



    def get_matches(self):
        return self.winners

    def get_allocations(self):
        return self.allocations

    def display_match_subgraph(self):
        '''Displays the NetworkX subgraph of the found matches'''
        pos = nx.circular_layout(self.matches_subgraph)
        nx.draw_networkx_edge_labels(self.matches_subgraph, pos)
        nx.draw_circular(self.matches_subgraph, with_labels=True)



    def match_tokens(self, model_elements, match_threshold, pos_list=["NOUN", "PROPN"]):
        '''Returns a list of matches between the tokens in the text and the list of model_elements
        Will match on the 'name' attribute of the model_elements dictionnaries'''

        self.transclusion_relations.clear()
        count=0
        # In all tokens
        for token in self.tokens:
            # Only POS of interest
            if token['pos'] in pos_list:

                found_match = None

                for element in model_elements:
                    count+=1
                    fuzzy_score = fuzzy_match_score(token['text'],  element['name'])

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
                    if pprint: print(el_i, el_j)
                    time1 = time.time()
                    try:
                        dist_ij = node_distance(g, el_i['uri'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', ''), el_j['uri'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', ''), pprint)
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

        cluster = order_clustering(self.matches_subgraph, max_k)

        for el_i in cluster:
            token_i_id = self.matches_subgraph.nodes(data=True)[el_i]['token']['token_id']
            if token_i_id not in winners:
                winners[token_i_id]=self.matches_subgraph.nodes(data=True)[el_i]

        self.winners = winners
        return winners


    def allocation_discovery(self, g):
        '''Discover allocations based on distance between the winners'''

        allocation_candidate = [candidate['model_element']['uri'] for candidate in self.winners.values()]

        for candidate in allocation_candidate:

            candidate_neighbors = get_node_neighbors(g, candidate.replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', ''))

            for neighbor in candidate_neighbors:

                if neighbor.id in allocation_candidate:
                    # Maybe we want more tuning there, to chose if we pop the neighbor or the candidate
                    # TODO: Score based on how many neighbors you have, etc.. 

                    allocation_candidate.pop(neighbor)

        self.allocations = allocation_candidate
        return allocation_candidate


    def insert_references(self):
        '''Inserts back the found references (winner) into the SPARQL graph'''
        insert_concat = """"""

        for winner in self.winners.values():
            insert_concat += INSERT_BLOCKS.format(input_uri = self.uri,
                                        input_text = self.text.replace('"', r'\"'),
                                        reference_uuid = uuid.uuid4().hex,
                                        match_uri = winner['model_element']['uri'],
                                        token_position = winner['token']['token_id'],
                                        token_text = winner['token']['text'].replace('"', r'\"'))

        insert_str = INSERT_QUERY.format(insert_blocks=insert_concat)

        self.sparql_wrapper.setMethod("POST")
        self.sparql_wrapper.setQuery(insert_str)


        results = self.sparql_wrapper.query()
        return results.response.read()


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
                    print('WARNING: Same age (0) and same token were merged\nToken:', G.nodes(data=True)[C1[1]]['token'])
                    cluster[n + t] = [t+1] + C1[1:] + C2[1:]
                else:
                    cluster[n + t] = [t+1] + C1[1:] + C2[1:]

    return cluster[n+t][1:]