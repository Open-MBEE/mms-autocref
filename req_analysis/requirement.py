import spacy
import networkx as nx
import numpy as np

from req_analysis.libs.metrics import fuzzy_match_score
from req_analysis.libs.neptune_wrapper import node_distance

import scipy
import scipy.spatial.distance as ssd
import scipy.cluster.hierarchy as hrchy

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
        c=0
        # In all req tokens
        for token in self.tokens:
            # Only POS of interest
            if token['pos'] in pos_list:

                found_match = None

                for element in model_elements:
                    c+=1
                    fuzzy_score = fuzzy_match_score(token['text'],  element['name'])

                    if fuzzy_score < match_threshold:

                        found_match = dict(token=token, model_element=element, score=fuzzy_score)
                        self.transclusion_relations.append(found_match)

        return self.transclusion_relations, c


    def init_match_subgraph(self, g):
        '''Initializes a NetworkX subgraph that contains all the couple (token, model_element_match) found and their edges are
        weighted on their distance in the model'''
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
        '''Uses the NetworkX req_subgraph and Scipy's linkage matrix to order the subgraph by
        hierarchical clustering order, and returns the correct matches'''

        k = 1
        max_k = self.req_subgraph.number_of_nodes()
        winners=dict()

        cluster = order_clustering(self.req_subgraph, max_k)

        for el_i in cluster:
            token_i_id = self.req_subgraph.nodes(data=True)[el_i]['token']['token_id']
            if token_i_id not in winners:
                winners[token_i_id]=self.req_subgraph.nodes(data=True)[el_i]
        
        return winners



# Clusters all the way and returns an ordonated list
def order_clustering(G, k):
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