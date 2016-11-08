from collections import namedtuple, defaultdict, deque
from error import *


class parser(object):
    """
    Checks the syntax of the file and strip off unnecessary tokens!
    The parser is very sensitive to indents!
    -----
    SYNTAX:

    -----

    DOCTEST:
    # >>> from generateTokens import *
    # >>> stream = open('../../samples/template.yml').readlines();
    # >>> t = tokenizer(stream);
    # >>> t.tokenize()
    # >>> tokens = t.tokens;
    # >>> p = parser(tokens)
    # >>> p.parse()
    #
    # If more than one HEADER found, throw ParseError:
    # >>> stream=['    PROPOSITION\\n','PROPOSITION\\n']
    # >>> t = tokenizer(stream); t.tokenize();
    # >>> p = parser(t.tokens)
    # >>> try:
    # ...     p.parse()
    # ... except ParseError:
    # ...     pass


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
        found = []
        headers = ['PROPOSITION', 'ARGUMENT',
                   'ASSUMPTION', 'PROOFSTANDARD', 'PARAMETER']
        previous_idx = len(self.tokens)  # starting from the back
        for idx, tok in reversed(list(enumerate(self.tokens))):
            # find tok_type = `STMT`, and check if it is one of the headers
            if tok.tok_type == 'STMT':
                if tok.c in headers and tok.c not in found:
                    # print('Found {} at {}, previous_idx = {}'.format(tok.c,
                    # idx, previous_idx))  # DEBUG

                    # store the start and stop indices:
                    if tok.c == 'PROPOSITION':
                        self.indices['PROPOSITION'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];

                    elif tok.c == 'ASSUMPTION':
                        self.indices['ASSUMPTION'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];

                    elif tok.c == 'ARGUMENT':
                        self.indices['ARGUMENT'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];

                    elif tok.c == 'PROOFSTANDARD':
                        self.indices['PROOFSTANDARD'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];

                    elif tok.c == 'PARAMETER':
                        self.indices['PARAMETER'] = [idx, previous_idx]
                        # toks = self.tokens[idx, previous_idx];

                    previous_idx = idx
                    found.append(tok.c)

                elif tok.c in found:
                    # prevent multiple usage of headers.
                    raise ParseError(
                        'More than one header of {} is found. Check that you only have one of each headers: {}'.format(tok.c, headers))


def generateStruct(toks, expect_depth):
    """
    generateStruct generates the structure of the tokens in the `toks` stream. The two strcuture supported are 1) in-line lists/sequence, 2) dictionarys/maps

    if there is a MAPPING_VALUE, and hence a map exists, a dict() is called and then it calls on generateStruct for the rest of the token streams.

    if there is a SEQUENCE_OPEN, and hence a list/sequence exists, a list() is used to store the list/sequence elements. The SEQUENCE_CLOSE token indicates the end of the sequence. Each element is separated by the SEQEUNCE_SEPARATOR token.
    """

    toks = deque(toks)  # use as a queue
    master = {}

    while len(toks):  # if there is still a token yet to be parsed:
        t = toks.popleft()
        t_type = t.tok_type

        if t_type == 'STMT':
            # find any more part of the STMT
            toks.appendleft(t)
            longsentence = find_STMT(toks)

            if expect_depth == -1:
                return longsentence

            # if the next token after STMT is MAPPING_VALUE, then we use this longsentence as a key
            # Otherwise, if indent is seen, it is an element to the current
            # key!
            try:
                t_next = toks.popleft()
            except IndexError:
                break

            if t_next.tok_type == 'MAPPING_VALUE':
                expect_depth += 1  # expect the next depth to be 1
                print(expect_depth)  # DEBUG
                master[longsentence] = generateStruct(toks, expect_depth)
                return master

        if t_type == 'INDENT':  # is an INDENT, add the value to the master
            depth = infer_depth(toks)

            # lookahead:
            t_next = toks.popleft()
            if depth == expect_depth and t_next.tok_type != 'MAPPING_VALUE':
                toks.appendleft(t_next)
                return generateStruct(toks, -1)  # add value

        # if t_type == 'INDENT':
        #     # if we found an indent, check it against the max_indent level.
        #     # if the indent level is a new max, create another dictionary
        #     # to host it
        #     depth = infer_depth(toks)
        #
        # elif
        #
        # elif t_type == 'MAPPING_VALUE':
        #     # use longsentence as the key of the dictionary
        #     master[longsentence] = {} # since it got to map to something!
        #     master_keys.append(longsentence)
        #
        #
        # if current_depth > max_depth:
        #     # a new indent level, then...
        #     key = master_keys[current_depth-1]
        #     master[key] = generateStruct(toks, current_depth)
        # else:
        #     pass


def generateList(toks):
    """
    When a SEQUENCE_OPEN is found in the stream of toks, generateList creates a list and add those STMT into the list.

    If a SEQUENCE_CLOSE is not found when no toks are left, an error is raised.

    >>> from generateTokens import Token; from collections import deque
    >>> S_OPEN = Token('[', 0,0, 'SEQUENCE_OPEN' )
    >>> S_CLOSE = Token(']', 0,1, 'SEQUENCE_CLOSE')
    >>> S_SEP = Token(',', 0,1, 'SEQEUNCE_SEPARATOR')
    >>> STMT = Token('item', 0,1, 'STMT')
    >>> MAPPING_VALUE = Token(':', 0,1, 'MAPPING_VALUE')

    >>> empty = deque([S_OPEN, S_CLOSE])
    >>> generateList(empty)
    []

    Error: No element in it but SEQEUNCE_SEPARATOR found
    >>> bad = deque([S_OPEN, S_SEP, S_CLOSE ])
    >>> try:
    ...     generateList(bad)
    ... except ParseError:
    ...     pass

    Good: two element
    >>> ok = deque([S_OPEN, STMT, S_SEP, STMT, S_CLOSE])
    >>> generateList(ok)
    ['item', 'item']

    Bad: mapping unit found
    >>> bad = deque([S_OPEN, STMT, MAPPING_VALUE, STMT, S_CLOSE])
    >>> try:
    ...     generateList(bad)
    ... except ParseError:
    ...     print('bad error')
    bad error
    """
    the_List = []
    t = toks.popleft()
    if t.tok_type == 'SEQUENCE_OPEN':
        found = 0
        num = 0 # count the number of sequence found
        while len(toks) and not found:  # if the token stream is not dry
            t = toks.popleft()
            if t.tok_type == 'SEQUENCE_CLOSE':
                # print('Number of item in list = {}'.format(str(num))) # DEBUG
                found = 1

                # check the number of elements in the list corresponds to the number of SEQEUNCE_SEPARATOR found:
                if num == 0:
                    if len(the_List)>1:
                        raise ParseError('{} SEQUENCE_SEPARATOR is found but none is expected'.format(str(num)))
                    else:
                        return the_List # empty list!
                else: # a separator found
                    expectation = len(the_List) -1
                    if expectation != num:
                        raise ParseError('{} SEQUENCE_SEPARATOR is found but none is expected'.format(num))
                    else:
                        return the_List # empty list!

            elif t.tok_type == 'SEQUENCE_OPEN':
                raise ParseError('[ found at line {} col {} before closing. Nesting of list is not allowed'.format(
                    t.lineIdx, t.colIdx))
            elif t.tok_type == 'MAPPING_VALUE':
                raise ParseError(
                    ': found at line {} col {} before closing.'.format(t.lineIdx, t.colIdx))
            elif t.tok_type == 'STMT':
                toks.appendleft(t);
                statement = find_STMT(toks)
                the_List.append(statement)
            elif t.tok_type == 'SEQEUNCE_SEPARATOR':
                num += 1;

    return the_List


def infer_depth(toks):
    """
    Given the remaining toks, infer the depth of this sentence
    depth = number of INDENT seen in the next few tokens until a MAPPING_VALUE or STMT is seen.

    One is added because of the one that has already been pop-ed
    """
    print('check depth')  # DEBUG
    depth = 1  # starts with 1 to include the one that already been pop-ed
    while len(toks):
        t = toks.popleft()

        if t.tok_type == 'INDENT':
            depth += 1
        else:
            toks.appendleft(t)
            break

    return depth


def find_STMT(toks):
    """
    Given a partial sentence, and toks, find the rest of STMT in the toks queue by iteratively calling popleft() and checking if the tok_type is STMT.
    If it is not (ie. the next tok in toks is "INDENT" or "MAPPING_VALUE"), then concatenate the sentence to form a longsentence and return it
    """
    # print('find STMT')  # DEBUG
    sentence = []
    while len(toks):
        t = toks.popleft()

        if t.tok_type == 'STMT':
            sentence.append(t)
        else:
            toks.appendleft(t)
            break

    get_c = lambda s: s.c  # lambda function to iteratively get the tyoe
    longsentence = [get_c(s) for s in sentence]
    # append white space between tokens to form a string.
    longsentence = ' '.join(longsentence)

    return longsentence


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
