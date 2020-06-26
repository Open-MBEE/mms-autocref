from nltk.metrics import jaccard_distance
from nltk.cluster.util import cosine_distance
from fuzzywuzzy import fuzz

import numpy as np
import string

import spacy
import en_core_web_sm
nlp = en_core_web_sm.load()
spacy_stopwords = spacy.lang.en.stop_words.STOP_WORDS


def fuzzy_match_score(str_1, str_2):
    '''Takes in 2 strings and return a fuzzy matching score'''

    fuzzy = 1 - (fuzz.ratio(str_1, str_2) / 100. )
    # jaccard = jaccard_distance(set(str_1.lower()), set(str_2.lower()))
    cosine = cosine_distance(vector_encode_letters(str_1), vector_encode_letters(str_2)) # This is 10 times slower than the other

    return fuzzy*cosine


def remove_stopwords_from_string(string):
    '''Takes in a string and removes all occurences of stopwords in it'''
    return ' '.join([token.text for token in nlp(string) if token.text.lower() not in spacy_stopwords])


def vector_encode_letters(n_gram, dictionnary=dict(zip(string.ascii_lowercase + '1234567890()-', range(39)))):
    '''Takes in an n-gram (or string) and encodes all the letters in it against alphabetical characters'''
    encoded_vector = np.zeros(len(dictionnary))
    for word in n_gram:
        for character in word:
            if character.lower() in dictionnary:
                encoded_vector[dictionnary[character.lower()]] += 1
    return encoded_vector
