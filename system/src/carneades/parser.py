from collections import  namedtuple
from error import *

class parser(object):
    """
    Checks the syntax of the file and strip off unnecessary tokens!
    The parser is very sensitive to indents!
    -----
    SYNTAX:

    -----

    DOCTEST:
    >>> from generateTokens import *
    >>> stream = open('../../samples/template.yml').readlines();
    >>> t = tokenizer(stream);
    >>> t.tokenize()
    >>> tokens = t.tokens;
    >>> p = parser(tokens)
    >>> p.parse()

    If more than one HEADER found, throw error:
    >>> stream=['    PROPOSITION\\n','PROPOSITION\\n']
    >>> t = tokenizer(stream); t.tokenize();
    >>> p = parser(t.tokens)
    >>> try:
    ...     p.parse()
    ... except ParseError:
    ...     pass


    """

    def __init__(self, tokens):
        self.tokens = tokens  # a list of tokens from the tokenizer
        # split the tokens according to the headers =  {PROPOSITION, ARGUMENT,
        # ASSUMPTION, PROOFSTANDARD, PARAMETER}
        self.proposition = []
        self.assumption = []
        self.argument = []
        self.proofstandard = []
        self.parameter = []
        self.indices = {'PROPOSITION': [0, 0],
                        'ASSUMPTION': [0, 0],
                        'ARGUMENT': [0, 0],
                        'PROOFSTANDARD': [0, 0],
                        'PARAMTER': [0, 0]
                        }

    def parse(self):
        """
        Split the tokens into the 5 main components of CAES:
        - PROPOSITION
        - ASSUMPTION
        - ARGUMENT
        - PROOFSTANDARD
        - PARAMETER
        """
        found = [];
        headers = ['PROPOSITION', 'ARGUMENT',
                   'ASSUMPTION', 'PROOFSTANDARD', 'PARAMETER']
        previous_idx = len(self.tokens) -1 # starting from the back
        for idx, tok in reversed(list(enumerate(self.tokens))):
            # find tok_type = `STMT`, and check if it is one of the headers
            if tok.tok_type == 'STMT':
                if tok.c in headers and tok.c not in found:
                    # print('Found {} at {}, previous_idx = {}'.format(tok.c, idx, previous_idx))  # DEBUG

                    # store the start and stop indices:
                    if tok.c == 'PROPOSITION':
                        self.indices['PROPOSITION'] = [idx, previous_idx]
                    elif tok.c == 'ASSUMPTION':
                        self.indices['ASSUMPTION'] = [idx, previous_idx]
                    elif tok.c == 'ARGUMENT':
                        self.indices['ARGUMENT'] = [idx, previous_idx]
                    elif tok.c == 'PROOFSTANDARD':
                        self.indices['PROOFSTANDARD'] = [idx, previous_idx]
                    elif tok.c == 'PARAMETER':
                        self.indices['PARAMETER'] = [idx, previous_idx]

                    previous_idx = idx-1;
                    found.append(tok.c)

                elif tok.c in found:
                    # prevent multiple usage of headers.
                    raise ParseError('More than one label of {} is found'.format(tok.c))

    def get_proposition(self):
        """
        find all the tokens that is relevant to proposition
        """
        

    def get_argument(self):
        """
        find all the tokens relevant to argument
        """

    def get_assumption(self):
        """
        find all the tokens relevant to assumption
        """

    def get_proofstandard(self):
        """
        find all the tokens relevant to proofstandard
        """

    def get_parameter(self):
        """
        find all the tokens relevant to parameter
        """


class indent_stack(object):
    """
    defines the stack to calculate indent level
    """



# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

DOCTEST = True

if __name__ == '__main__':
    """
    """
    # if DOCTEST:
    import doctest
    print('Starting doctest!')
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
