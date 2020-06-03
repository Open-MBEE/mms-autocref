import spacy
import networkx as nx
from req_analysis.libs.metrics import fuzzy_match_score
from req_analysis.libs.neptune_wrapper import node_distance

from paris import paris
from paris.utils import select_clustering

import scipy
import scipy.spatial.distance as ssd

import time

nlp_np = spacy.load("en_core_web_sm")
merge_nps = nlp_np.create_pipe("merge_noun_chunks")
nlp_np.add_pipe(merge_nps)



class Requirement():


    def __init__(self, uri, req_text):
        self.text_uri = uri
        self.text = req_text
        self.tokens = []
        self.transclusion_relations = []

        for token in nlp_np(self.text):
            self.tokens.append(dict(text=token.text, pos=token.pos_, token_id=token.i))

        self.req_subgraph = None


    def match_req_tokens(self, model_elements, match_threshold, pos_list=["NOUN", "PROPN"]):
        '''Takes in a Requirement object and optional configuration
        Returns a list of matches between the tokens in the requirement and the list of model_elements
        Will match on the 'name' attribute of the model_elements dictionnaries'''

        self.transclusion_relations.clear()

        # In all req tokens
        for token in self.tokens:
            # Only POS of interest
            if token['pos'] in pos_list:

                found_match = None

                for element in model_elements:
                    
                    fuzzy_score = fuzzy_match_score(token['text'],  element['name'])

                    if fuzzy_score < match_threshold:

                        found_match = dict(token=token, model_element=element, score=fuzzy_score)
                        self.transclusion_relations.append(found_match)

        return self.transclusion_relations


    def init_match_subgraph(self, g):
        number_matches = len(self.transclusion_relations)
        req_subgraph = nx.Graph()

        # We want one node per matched token and not per model element matched
        # The more it is referenced, the more important it is (if the text says 'APS' 10 times, APS has to be important)
        for i in range(number_matches):
            req_subgraph.add_node(i, **self.transclusion_relations[i])

        for i in range(number_matches):
            for j in range(i+1, number_matches):
                el_i, el_j = self.transclusion_relations[i]['model_element'], self.transclusion_relations[j]['model_element']

                if el_i == el_j:
                    dist_ij = 0.1
                    print(i, j)
                    print('The 2 model elements are the same')
                else:
                    print(i, j)
                    print(el_i, el_j)
                    time1 = time.time()
                    try:
                        dist_ij = node_distance(g, el_i['uri'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', ''), el_j['uri'].replace('https://opencae.jpl.nasa.gov/mms/rdf/element/', ''))
                        print()
                        print('SUCCESS in ', time.time()-time1, 's ', dist_ij)
                    except:
                        print('FAILURE in ', time.time()-time1, 's:  ')
                        dist_ij = 11
                    print('_________')

                # We use 1/dist_ij because the Paris algorithm uses higher_weight=greater_proximity convention
                req_subgraph.add_edge(i, j, weight=dist_ij)

        self.req_subgraph = req_subgraph
        return req_subgraph


    def match_clustering(self):


        linkage_array = scipy.cluster.hierarchy.linkage(ssd.squareform(nx.to_numpy_matrix(self.req_subgraph)))
        looper = True
        k = 1
        max_k = self.req_subgraph.number_of_nodes()

        print(linkage_array)

        while looper and k < max_k:

            L = select_clustering(linkage_array, k)
            looper = self.check_continue(select_clustering(linkage_array, k+1))
            k += 1

        print(L)
        return L


    
    def check_continue(self, L):
        '''Takes in a list returned by select_clustering and checks that no cluster has 2 times the same token in it'''
        
        # For each cluster
        for cluster in L:

            # checks that no 2 nodes in the cluster has the same source token
            for i in range(len(cluster)):
                token_i = self.req_subgraph.nodes(data=True)[cluster[i]]['token']
                for j in range(i+1, len(cluster)):

                    token_j = self.req_subgraph.nodes(data=True)[cluster[j]]['token']

                    if token_i['token_id']==token_j['token_id']:
                        return False

        return True
