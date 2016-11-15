from collections import deque
from error import ParseError
# -------------------------------------------------------------------------
# :class: parser
# :class: Node
# :def: generateStruct
# :def: find_chunks_depth
# :def: find_STMT
# :def: find_SEQUENCE
# :def: infer_depth
# -------------------------------------------------------------------------


class Parser(object):
    """
    Checks the syntax of the file and strip off unnecessary tokens!
    The parser is very sensitive to indents!

    -------
    DOCTEST:
    -------
    >>> from tokenizer import Tokenizer
    >>> stream = open('../../samples/example.yml').readlines();
    >>> t = Tokenizer(stream);
    >>> p = Parser(t.tokens)
    >>> p.proposition.children
    [murder, kill, intent, witness1, witness2, unreliable1, unreliable2]
    >>> p.assumption.children
    ['kill', 'witness1', 'witness2', 'unreliable2']
    >>> p.argument.children
    [is there an intent to murder?, is witness1 sufficient to proof intent?, is witness2 sufficient to proof intent?]
    >>> p.argument.find_child('is witness2 sufficient to proof intent?')
    is witness2 sufficient to proof intent?
    >>> p.argument.find_child('is witness2 sufficient to proof intent?').children
    [premise, exception, conclusion, weight]
    >>> p.argument.find_child('is witness2 sufficient to proof intent?').find_child('conclusion').children[0].data
    '-intent'
    >>> p.parameter.children
    [alpha, beta, gamma]
    >>> p.acceptability.children
    ['murder', '-murder']


    If more than one HEADER found, throw ParseError:
    >>> stream=['    PROPOSITION\\n','PROPOSITION\\n']
    >>> t = Tokenizer(stream);
    >>> try:
    ...     Parser(t.tokens)
    ... except ParseError:
    ...     pass

    """

    def __init__(self, tokens):
        """
        Create a parser for the stream of tokens.
        When initiailised, the parser will call self.parse() to parse the tokens into the components.

        If the headers are not found, or more than one of each type of label is found, an error will be raised.

        """
        self.tokens = tokens
        self.proposition = None
        self.assumption = None
        self.argument = None
        self.parameter = None
        self.acceptability = None
        self.proofstandard = None
        self.parse()

    def parse(self):
        """
        Split the tokens into the 5 main components of CAES:
        - PROPOSITION
        - ASSUMPTION
        - ARGUMENT
        - PARAMETER
        """
        found = set()  # set that contains the headers found
        headers = ['PROPOSITION', 'ARGUMENT', 'ASSUMPTION', 'PARAMETER', 'ACCEPTABILITY', 'PROOFSTANDARD']
        previous_idx = len(self.tokens)  # starting from the back
        for idx, tok in reversed(list(enumerate(self.tokens))):
            # find tok_type = `STMT`, and check if it is one of the headers
            if tok.tok_type == 'STMT' and tok.c in headers:
                if tok.c not in found:
                    # call generateStruct to create nodes for each headers
                    if tok.c == 'PROPOSITION':
                        toks = self.tokens[idx: previous_idx]
                        self.proposition = self.generateStruct(toks)

                    elif tok.c == 'ASSUMPTION':
                        toks = self.tokens[idx: previous_idx]
                        self.assumption = self.generateStruct(toks)

                    elif tok.c == 'ARGUMENT':
                        toks = self.tokens[idx: previous_idx]
                        self.argument = self.generateStruct(toks)

                    elif tok.c == 'PARAMETER':
                        toks = self.tokens[idx: previous_idx]
                        self.parameter = self.generateStruct(toks)

                    elif tok.c == 'ACCEPTABILITY':
                        toks = self.tokens[idx: previous_idx]
                        self.acceptability = self.generateStruct(toks)

                    elif tok.c == 'PROOFSTANDARD':
                        toks = self.tokens[idx: previous_idx]
                        self.proofstandard = self.generateStruct(toks)

                    previous_idx = idx  # update the index so that the next header's indices will not include those of the previous header
                    found.add(tok.c)  # maintain a list of this that is found

                elif tok.c in found:
                    # prevent multiple usage of headers!
                    raise ParseError(
                        'More than one header of {} is found. Check that you only have one of each headers: {}'.format(tok.c, headers))

        if len(found) != len(headers):
            raise ParseError(
                'Expected labels are: {}. However, only {} fonud.'.format(headers, found))

    def generateStruct(self, toks):
        """
        generateStruct generates the structure of the tokens in the `toks` stream. The two strcuture supported are 1) in-line lists/sequence, 2) dictionarys/maps

        if there is a MAPPING_VALUE, and hence a map exists, a dict() is called and then it calls on generateStruct for the rest of the token streams.

        if there is a SEQUENCE_OPEN, and hence a list/sequence exists, a list() is used to store the list/sequence elements. The SEQUENCE_CLOSE token indicates the end of the sequence. Each element is separated by the SEQUENCE_SEPARATOR token.
        """

        toks = deque(toks)  # use as a queue
        root = None

        t = toks.popleft()
        t_type = t.tok_type

        # ------------------------------------------------------------------
        #       A stream of tokens belonging to STMT will be followed
        # ------------------------------------------------------------------

        if t_type == 'STMT':
            # find any more part of the STMT
            toks.appendleft(t)
            toks, longsentence = find_STMT(toks)  # find the string

            if len(toks) == 0:
                # no more tokens left to processed (e.g end of a sentence)
                return longsentence

            else:  # more tokens left to be processed:
                t_next = toks.popleft()

                # We will exepct a MAPPING_VALUE first:
                if t_next.tok_type is 'MAPPING_VALUE':
                    root = Node(longsentence)  # create the root node
                else:
                    raise ParseError('MAPPING_VALUE (:) is expected at line {} col {} `{}`. Instead, {} is found!'.format(
                        t_next.lineIdx, t_next.colIdx, t.c, t_next.c))

                # ----------------------------------------------------------
                #       And find the children of the root:
                #       - a map of stuffs
                #       or ends with:
                #           - a children is either a list/sequence
                #           - or a sentence
                # ----------------------------------------------------------
                try:
                    t_next = toks.popleft()
                except IndexError:
                    raise ParseError("Incomplete syntax found at line {} col {}".format(t_next.lineIdx, t_next.colIdx))

                if t_next.tok_type == 'SEQUENCE_OPEN':
                    # a sequence list is given
                    toks.appendleft(t_next)
                    toks, the_List = find_SEQUENCE(toks)
                    root.add_child(the_List)  # node will create a child node
                    return root

                elif t_next.tok_type == 'STMT':
                    toks.appendleft(t_next)
                    toks, the_List = find_STMT(toks)
                    root.add_child(the_List)  # node will create a child node
                    return root

                # ----------------------------------------------------------
                #   When an indent is found, it suggests that there are sub items
                #   in belonging to this node. using `find_args_depth`, we retrieve
                #   a list of nodes belonging to this level.
                #   Each nodes will end up as the children of the root node.
                #
                #   find_args_depth iterateively calls `generateStruct`
                #   to create these nodes
                # ----------------------------------------------------------
                #
                elif t_next.tok_type == 'INDENT':  # is an INDENT, add the value to the master node
                    toks.appendleft(t_next)
                    depth = infer_depth(toks)
                    # call find_args_depth to get the tokens that belongs to the
                    # this key
                    chunks = find_chunks_depth(toks, depth)
                    for chunk in chunks:
                        root.add_child(self.generateStruct(chunk))
        return root

# ---------------------------------------------------------------------------


class Node(object):
    """
    Nodes have children and contain data about itself, it uses `list()` to hold the multiple children

    >>> root = Node('ARGUMENT')
    >>> root.add_child(['one','two','three'])
    >>> root.children
    ['one', 'two', 'three']

    # An example of the PARAMETER header used in the source file.
    >>> root = Node('PARAMETER')
    >>> alpha = Node('alpha'); alpha.add_child(0.3)
    >>> beta = Node('beta'); beta.add_child(0.2)
    >>> gamma = Node('gamma'); beta.add_child(0.1)
    >>> root.add_child(alpha)
    >>> root.add_child(beta)
    >>> root.add_child(gamma)
    >>> root.children
    [alpha, beta, gamma]
    >>> root.find_child('beta')
    beta
    >>> try:
    ...     root.find_child('hamma')
    ... except ParseError:
    ...     pass
    """

    def __init__(self, data):
        self.data = data
        self.children = []

    def add_child(self, child_data):
        # create node for child: using child as data
        if type(child_data) is Node:
            self.children.append(child_data)
        else:
            if type(child_data) is list:  # if it is already a list, extend the list of children
                self.children.extend(child_data)
            else:
                # otherwise if is just a word/statement, add it to the list
                child_node = Node(child_data)
                self.children.append(child_node)

    def find_child(self, value):
        """
        Given the data of the child, iteratively search the Node's children. Once found, return that node.

        """
        queue = deque(
            self.children)  # add the list of children (nodes) into the queue
        # visited = set()

        while len(queue) > 0:
            this_node = queue.pop()
            # if this_node in visited:
            #     continue  # start from the next item in queue

            # unique value:
            # visited.add(child)
            # if type(this_node.data) is list:
            #     for ele in this_node.data:
            #         if ele == value:
            #             return this_node
            # else:
            if this_node.data == value:
                return this_node

            for child_node in this_node.children:  # breath first search
                # if child_node not in visited:
                queue.appendleft(child_node)

        # throw error if not found
        raise ParseError('{} not found in {}'.format(
            value, self))

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__str__() == other

    def __hash__(self):
        return hash(self.data)


# ---------------------------------------------------------------------------
#       Helper functions
# ---------------------------------------------------------------------------
def find_chunks_depth(toks, expected_depth):
    """
    Given a certain :param: depth and a stream of :param: toks, find_chunks_depth returns a list of :class: Node at :param: depth

    Mechanism:
    take the expected_depth (e.g.1):
    if the toks have an INDENT token (hence depth of 1), then that is the 'root' node. everything with the more than the expected_depth is the children of the node.

    So, while parsing the toks, if another token have only one INDENT (or of similar expected_depth), it must be another chunk (another root node)

    >>> from tokenizer import Token; from collections import deque
    >>> ind = Token('  ', 1,0, 'INDENT')
    >>> stmt = Token('asd', 1,0, 'STMT')
    >>> toks = [ind, stmt, ind, ind, stmt]; toks = deque(toks)
    >>> find_chunks_depth(toks, 1)
    [deque([STMT, INDENT, STMT])]

    >>> toks = [ind, stmt, ind, ind, stmt, ind, ind, stmt]; toks = deque(toks)
    >>> find_chunks_depth(toks, 1)
    [deque([STMT, INDENT, STMT, INDENT, STMT])]

    # two blocks
    >>> toks = [ind, stmt, ind, ind, stmt, ind, ind, stmt, ind, stmt, ind, ind, stmt]; toks = deque(toks)
    >>> find_chunks_depth(toks, 1)
    [deque([STMT, INDENT, STMT, INDENT, STMT]), deque([STMT, INDENT, STMT])]

    # if a depth lower than the expected_depth is found, stop and return
    >>> deep_blocks = [ind, ind, stmt, ind, ind, stmt, ind, stmt]; toks=deque(deep_blocks)
    >>> find_chunks_depth(toks, 2)
    [deque([STMT]), deque([STMT])]
    """
    chunks = []
    handling = False

    while len(toks):

        if handling:  # found a block, and extracting its elemnts
            if toks[0].tok_type == 'INDENT':

                # find the depth of the nearest line
                this_depth = infer_depth(toks)

                if this_depth > expected_depth:  # sub blocks
                    num = expected_depth
                    while num:  # pop only the expected number of indents
                        toks.popleft()
                        num -= 1

                    delta = this_depth - expected_depth
                    while delta:  # add the remaining indents into the chunk
                        chunk.append(toks.popleft())
                        delta -= 1  # remaining of indents left to add

                if this_depth < expected_depth:
                    break

                if this_depth == expected_depth:
                    chunks.append(chunk)
                    handling = False  # found another block!
                    continue

            else:  # other token types
                chunk.append(toks.popleft())  # add them to the chunk

        else:  # not handling any blocks - the start state of this function
            if toks[0].tok_type == 'INDENT':

                this_depth = infer_depth(toks)

                if this_depth == expected_depth:
                    # if handling is true, then this will indicate a new block
                    handling = True
                    chunk = deque([])

                    while this_depth:
                        toks.popleft()  # remove all the INDENT tokens
                        this_depth -= 1

    chunks.append(chunk)
    return chunks


def find_SEQUENCE(toks):
    """
    When a SEQUENCE_OPEN is found in the stream of toks, find_SEQUENCE creates a list and add those STMT into the list.

    If a SEQUENCE_CLOSE is not found when no toks are left, an error is raised.

    DOCTEST for find_SEQUENCE:
    ---
    >>> from tokenizer import Token; from collections import deque
    >>> S_OPEN = Token('[', 0,0, 'SEQUENCE_OPEN' )
    >>> S_CLOSE = Token(']', 0,1, 'SEQUENCE_CLOSE')
    >>> S_SEP = Token(',', 0,1, 'SEQUENCE_SEPARATOR')
    >>> STMT = Token('item', 0,1, 'STMT')
    >>> MAPPING_VALUE = Token(':', 0,1, 'MAPPING_VALUE')

    >>> empty = deque([S_OPEN, S_CLOSE])
    >>> toks, the_list = find_SEQUENCE(empty)
    >>> toks
    deque([])
    >>> the_list
    []

    Error: No element in it but SEQUENCE_SEPARATOR found
    >>> bad = deque([S_OPEN, S_SEP, S_CLOSE ])
    >>> try: find_SEQUENCE(bad)
    ... except ParseError: pass

    Good: two element
    >>> ok = deque([S_OPEN, STMT, S_SEP, STMT, S_CLOSE])
    >>> toks, the_list = find_SEQUENCE(ok)
    >>> toks
    deque([])
    >>> the_list
    ['item', 'item']

    Bad: mapping unit found
    >>> bad = deque([S_OPEN, STMT, MAPPING_VALUE, STMT, S_CLOSE])
    >>> try:
    ...     find_SEQUENCE(bad)
    ... except ParseError:
    ...     print('bad error')
    bad error
    """

    the_List = []
    t = toks.popleft()
    if t.tok_type == 'SEQUENCE_OPEN':
        found = 0
        num = 0  # count the number of sequence found

        while len(toks) and not found:  # if the token stream is not dry

            t = toks.popleft()

            if t.tok_type == 'SEQUENCE_CLOSE':
                # print('Number of item in list = {}'.format(str(num))) # DEBUG
                found = 1

                # check the number of elements in the list corresponds to the
                # number of SEQUENCE_SEPARATOR found:
                if num == 0:
                    if len(the_List) > 1:
                        raise ParseError(
                            '{} SEQUENCE_SEPARATOR is found but none is expected'.format(str(num)))
                    else:
                        return toks, the_List  # empty list!
                else:  # a separator found
                    expectation = len(the_List) - 1
                    if expectation != num:
                        raise ParseError(
                            '{} SEQUENCE_SEPARATOR is found but none is expected'.format(num))
                    else:
                        return toks, the_List  # empty list!

            elif t.tok_type == 'SEQUENCE_OPEN':
                raise ParseError('[ found at line {} col {} before closing. Nesting of list is not allowed'.format(
                    t.lineIdx, t.colIdx))

            elif t.tok_type == 'MAPPING_VALUE':
                raise ParseError(
                    ': found at line {} col {} before closing.'.format(t.lineIdx, t.colIdx))

            elif t.tok_type == 'STMT':
                toks.appendleft(t)
                toks, statement = find_STMT(toks)
                the_List.append(statement)

            elif t.tok_type == 'SEQUENCE_SEPARATOR':
                num += 1

        raise ParseError(
            'Unable to parse the stream at line {}'.format(t.lineIdx))


def infer_depth(toks):
    """
    Given the remaining toks, infer the depth of this sentence
    depth = number of INDENT token(s) found in the stream of tokens until a MAPPING_VALUE or STMT is seen.
    One is added because of the one that has already been pop-ed

    DOCTESET to see if an error is thrown if the string is just all indent!
    >>> from tokenizer import Token; from collections import deque;
    >>> indent = Token('  ', 1,0, 'INDENT')
    >>> toks = deque([indent, indent, indent])
    >>> infer_depth(toks)
    3
    """
    # print('check depth')  # DEBUG
    depth = 0  # starts with 1 to include the one that already been pop-ed
    i = 0
    while len(toks):
        try:
            t = toks[i]
        except IndexError:
            break

        if t.tok_type == 'INDENT':
            depth += 1
            i += 1
        else:
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
        else:  # something that is not STMT, stop and return
            toks.appendleft(t)
            break

    get_c = lambda s: s.c  # lambda function to iteratively get the tyoe
    longsentence = [get_c(s) for s in sentence]
    # append white space between tokens to form a string.
    longsentence = ' '.join(longsentence)
    return toks, longsentence

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

DOCTEST = True

if __name__ == '__main__':
    """
    Run the doctest!
    """
    # if DOCTEST:
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
