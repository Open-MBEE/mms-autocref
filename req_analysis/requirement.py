import spacy

from req_analysis.libs.neo4j_wrapper import get_weighted_neighbors
from req_analysis.libs.metrics import fuzzy_match_score

nlp_np = spacy.load("en_core_web_sm")
merge_nps = nlp_np.create_pipe("merge_noun_chunks")
nlp_np.add_pipe(merge_nps)



class Requirement():


    def __init__(self, req_id, req_text):
        self.uuid = req_id
        self.text = req_text
        self.tokens = []
        self.transclusion_relations = []

        for token in nlp_np(self.text):
            self.tokens.append(dict(text=token.text, pos=token.pos_))



    def match_req_tokens(self, model_elements, match_threshold, pos_list=["NOUN", "PROPN"]):
        '''Takes in a Requirement object and optional configuration
        Returns a list of matches between the tokens in the requirement and the rest of the model
        Will match on the 'name' attribute of the model elements'''

        # In all req tokens
        for token in self.tokens:
            # Only POS of interest
            if token['pos'] in pos_list:

                found_match = None

                for element in model_elements:
                    
                    fuzzy_score = fuzzy_match_score(token['text'],  element)

                    if fuzzy_score < match_threshold:

                        if found_match == None:
                            found_match = dict(token=token['text'], model_element=element, score=fuzzy_score)
                        elif fuzzy_score < found_match['score']:
                            found_match = dict(token=token['text'], model_element=element, score=fuzzy_score)

                if found_match != None:
                    self.transclusion_relations.append(found_match)

        return self.transclusion_relations
