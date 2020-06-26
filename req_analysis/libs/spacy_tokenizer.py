import re
import spacy
from spacy.tokenizer import Tokenizer
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex
from spacy import util
from spacy.lang.tokenizer_exceptions import TOKEN_MATCH
from spacy.tokens import Token
# Token.set_extension('tag', default=False)


def create_custom_tokenizer(nlp):
    
    infixes = tuple([r"\<[\w\/]*\>"]) +  nlp.Defaults.infixes
    prefixes = tuple([r"\<[\w\/]*\>"]) +  nlp.Defaults.prefixes
    suffixes = tuple([r"\<[\w\/]*\>"]) +  nlp.Defaults.suffixes
    infix_re = spacy.util.compile_infix_regex(infixes)
    prefix_re = compile_prefix_regex(prefixes)
    suffix_re = compile_suffix_regex(suffixes)

    return Tokenizer(nlp.vocab, prefix_search=prefix_re.search,
                                suffix_search=suffix_re.search,
                                infix_finditer=infix_re.finditer,
                                token_match=nlp.tokenizer.token_match,
                                rules=nlp.Defaults.tokenizer_exceptions)
