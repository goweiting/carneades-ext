from collections import  namedtuple, defaultdict, deque
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

    If more than one HEADER found, throw ParseError:
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
        previous_idx = len(self.tokens) # starting from the back
        for idx, tok in reversed(list(enumerate(self.tokens))):
            # find tok_type = `STMT`, and check if it is one of the headers
            if tok.tok_type == 'STMT':
                if tok.c in headers and tok.c not in found:
                    # print('Found {} at {}, previous_idx = {}'.format(tok.c, idx, previous_idx))  # DEBUG

                    # store the start and stop indices:
                    if tok.c == 'PROPOSITION':
                        self.indices['PROPOSITION'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];
                        # self.get_proposition(toks);

                    elif tok.c == 'ASSUMPTION':
                        self.indices['ASSUMPTION'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];
                        # self.get_assumption(toks);

                    elif tok.c == 'ARGUMENT':
                        self.indices['ARGUMENT'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];
                        # self.get_argument(toks);

                    elif tok.c == 'PROOFSTANDARD':
                        self.indices['PROOFSTANDARD'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];
                        # self.get_proofstandard(toks);

                    elif tok.c == 'PARAMETER':
                        self.indices['PARAMETER'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];
                        # self.get_parameter(toks);

                    previous_idx = idx;
                    found.append(tok.c)

                elif tok.c in found:
                    # prevent multiple usage of headers.
                    raise ParseError('More than one header of {} is found. Check that you only have one of each headers: {}'.format(tok.c, headers))

    def get_proposition(self, toks):
        """
        find all the tokens that is relevant to proposition
        """


    def get_argument(self, toks):
        """
        find all the tokens relevant to argument
        """

    def get_assumption(self, toks):
        """
        find all the tokens relevant to assumption
        """

    def get_proofstandard(self, toks):
        """
        find all the tokens relevant to proofstandard
        """

    def get_parameter(self, toks):
        """
        find all the tokens relevant to parameter
        """


def generateStruct(toks):
    toks = deque(toks); # use as a queue
    level = 0;
    tree = tree();
    # longsentence = sentence.join(' '); # add space between words

    while len(toks): # if len(toks)==0 == False
        current_tok = toks.popleft()
        stack_count = 0

        if t.tok_type == 'STMT':
            try:
                struct[stack_count].append(t);
            except KeyError:
                struct[stack_count] = {};
                struct[stack_count]

        elif t.tok_type == 'MAPPING_VALUE': # Expect indent next

            if toks[stack_count].tok_type != 'INDENT':
                raise ParseError('Expect indent after MAPPING_VALUE, : in line {} col {}'.format(t.lineIdx, t.colIdx))
            else:
                while toks.popleft().tok_type == 'INDENT':
                    stack_count += 1;

def tree():
    return defaultdict(tree)

class Node(object):
    """
    The node of the tree
    """
    def __init__(self, level, data):
        self.data = data
        self.level = level
        self.children = []

    def add_children(self, level, data):
        child = Node(level, data) # the child is a node it self
        # if levself.level
        self.children.append(child)


class Tree(object):
    """
    Tree data structure to hold nodes
    """
    def __init__(self):
        """
        Tree to keep track of its own depth and number of elements
        """
        self.levels = dict();
        self.num_nodes = 0;
        self.depth = -1;

    def add_node(self, node):
        lev = node.level;

        if lev > self.depth:
            self.levels[lev] = []
            self.levels[lev].append(node)
            self.depth = lev
        else:
            self.levels[lev].append(node)



# class indent_stack(object):
#     """
#     defines the stack to calculate indent level
#     """
#     def __init__ (self):
#         self.list = list();
#
#     def get_depth(self):
#
#     def add(self):
#         self.list.append(1);

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
