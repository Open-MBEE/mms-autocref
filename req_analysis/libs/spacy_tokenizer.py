import re
import spacy
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex
from spacy import util
from spacy.lang.tokenizer_exceptions import TOKEN_MATCH
from spacy.tokens import Token



def create_custom_tokenizer(nlp):
    
    infixes = tuple([r"\<[\w\/]*\>"]) +  nlp.Defaults.infixes
    infix_re = spacy.util.compile_infix_regex(infixes)

    prefixes = list(nlp.Defaults.prefixes)
    prefixes.remove('<')
    prefixes = tuple(prefixes)
    suffixes = list(nlp.Defaults.suffixes)
    suffixes.remove('>')
    suffixes = tuple(suffixes)
    prefix_search = (util.compile_prefix_regex(prefixes).search)
    suffix_search = (util.compile_suffix_regex(suffixes).search)

    return Tokenizer(nlp.vocab, prefix_search=prefix_search,
                                suffix_search=suffix_search,
                                infix_finditer=infix_re.finditer,
                                token_match=None)
