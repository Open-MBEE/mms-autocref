import spacy
from py2neo import Node, Relationship

from req_analysis.lib.neo4j_wrapper import get_weighted_neighbors
from req_analysis.lib.metrics import fuzzy_match_score

nlp_np = spacy.load("en_core_web_sm")
merge_nps = nlp_np.create_pipe("merge_noun_chunks")
nlp_np.add_pipe(merge_nps)



class Requirement():


    def __init__(self, model, req_node):
        self.model = model
        self.node = req_node
        self.name = req_node['name']
        self.uuid = req_node['uuid']
        self.text = req_node['req_text'] or ''
        self.doc_np = nlp_np(self.text)
        self.phrase_node = None
        self.phrase_relation = None
        self.token_nodes = []
        self.token_relations = []
        self.transclusion_relations = []
        self.transcluded_text = None


    def init_req_nodes(self):
        # TODO: Maybe include that in the __init__ ?
        '''Initializes the phrase/token nodes and relations of the requirement'''
        req_phrase_node = Node("ReqPhrase", req_text=self.text)
        self.phrase_node = req_phrase_node
        self.phrase_relation = (Relationship(self.node, "IS", req_phrase_node))

        req_doc = nlp_np(self.text)

        for token in req_doc:
            token_node = Node("ReqChunk", chunk=token.text, pos=token.pos_)

            self.token_nodes.append(token_node)
            self.token_relations.append(Relationship(req_phrase_node, "IS_COMPOSED_OF", token_node))


    def match_req_tokens(self, pos_list=["NOUN", "PROPN"], relationship_filter='PART|TYPED|ALLOCATED|_', label_filter='', min_level=1, max_level=8, weighted_depth_limit=8):
        '''Takes in a Requirement object and optional configuration
        Returns a list of matches between the tokens in the requirement and the rest of the model
        Will match on the 'name' attribute of the model elements'''

        # This will return a dict with the neighbors of the req_node, ordered by weighted_depth 
        # Might be optimizable by not calling .data() and iterating on the cursor.. not sure, not essential for now
        neighbor_dict = get_weighted_neighbors(self.model.graph, self.node, weighted_depth_limit, relationship_filter, label_filter, min_level, max_level).data()

        # In all req tokens
        for token_node in self.token_nodes:
            # Only POS of interest
            if token_node['pos'] in pos_list:

                found_match = None
                # For an increasing weighted_depth
                for neighbor in neighbor_dict:

                    if found_match!=None:
                        break

                    # Iterate through all n-degree neighbors
                    for neighbor_node in neighbor['nodes_at_depth']:

                        # Nothing restricts neighbor_node to have a name but the way the graph was generated, so we may want to catch eceptions
                        try:
                            fuzzy_score = fuzzy_match_score(token_node['chunk'],  neighbor_node['name'])
                        except:
                            print('Unexpected Behavior: neighbor_node has no name attribute: ', neighbor_node)
                            break

                        if fuzzy_score < self.model.match_threshold:

                            if found_match == None:
                                found_match = dict(token_node=token_node, neighbor_node=neighbor_node, score=fuzzy_score)
                            elif fuzzy_score < found_match['score']:
                                found_match = dict(token_node=token_node, neighbor_node=neighbor_node, score=fuzzy_score)

                if found_match != None:
                    self.transclusion_relations.append(found_match)



    def init_transcluded_text(self):
        '''Initializes the transcluded_text for a requirement that already has transcluded_relations'''
        text_chunks = [node['chunk'] for node in self.token_nodes]
        print()
        for transclusion in self.transclusion_relations:
            index = self.token_nodes.index(transclusion['token_node'])
            transcluded_qualified_name = self.model.get_qualified_name(transclusion['neighbor_node'])
            text_chunks[index] = "<cref id='" + transcluded_qualified_name + "'>" + text_chunks[index] + "</cref>"
        self.transcluded_text = ' '.join(text_chunks)



    def context_cluster_scoring(self, context_cluster, pos_list=["NOUN", "PROPN"]):
        '''Takes in a ContextCluster and returns the match score between the Requirement and the ContextCluster'''
        context_score = 0

        # In all req tokens
        for token_node in self.token_nodes:
            # Only POS of interest
            if token_node['pos'] in pos_list:

                # SOURCE NODE
                fuzzy_score_source = fuzzy_match_score(token_node['chunk'], context_cluster.source_node['name'])
                if fuzzy_score_source < self.model.match_threshold:
                    print('... SOURCE NODE MATCH: ', token_node['chunk'], context_cluster.source_node['name'])
                    context_score += (2 - fuzzy_score_source)

                # CONTEXT
                else:
                    for cluster_node in context_cluster.context:

                        # Nothing restricts neighbor_node to have a name but the way the graph was generated, so we may want to catch eceptions
                        try:
                            fuzzy_score = fuzzy_match_score(token_node['chunk'],  cluster_node['name'])
                        except:
                            print('Unexpected Behavior: neighbor_node has no name attribute: ', cluster_node)
                            break

                        # If we find a match, increment score and break out of {for cluster_node} loop
                        if fuzzy_score < self.model.match_threshold:
                            print('... CONTEXT MATCH: ', token_node['chunk'],  cluster_node['name'], context_cluster.source_node)
                            context_score += (1 - fuzzy_score)
                            break
        return context_score



    def context_cluster_mapping(self):
        '''Loops through all ContextClusters of the model and returns the ContextCluster that has the highest score
        Its source_node will be the target of the Allocation'''
        max_score = 0
        allocation_target = None

        for context in self.model.contexts:
            current_score = self.context_cluster_scoring(context)
            if current_score > max_score:
                max_score = current_score
                allocation_target = context
        return allocation_target
