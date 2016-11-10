import re
from carneades.error import TokenizerError


# ---------------------------------------------------------------------------
class Tokenizer(object):
    """
    Takes in a stream of character and tokenize them according to the rule
    ---
    DOCTEST:
    Every stream is just a list of one str for modularised testing
    >>> stream = ['Hello World# IGNORE MY COMMENT ! ##\\n', ':\\n', '\\n']
    >>> t = Tokenizer(stream)
    >>> t.tokens
    [STMT, STMT, MAPPING_VALUE]

    Ill form (no End of line)
    >>> stream = ['A sequence : ', '  - An indent expected here!']
    >>> try: t = Tokenizer(stream)
    ... except TokenizerError: pass

    Indent detector
    >>> stream = ['A sequence : \\n', '  An indent expected here!\\n', '    nested indents\\n']
    >>> t = Tokenizer(stream) # use default indent_size = 2
    >>> t.tokens
    [STMT, STMT, MAPPING_VALUE, INDENT, STMT, STMT, STMT, STMT, INDENT, INDENT, STMT, STMT]
    >>> stream = ['   Testing with 3 spaces as indent\\n']
    >>> try : t = Tokenizer(stream)
    ... except TokenizerError: pass
    >>> t = Tokenizer(stream, 3)
    >>> t.tokens
    [INDENT, STMT, STMT, STMT, STMT, STMT, STMT]

    Sequence separator:
    >>> Stream = ["ASSUMPTION : [ ONE , TWO , THREE ]\\n"]
    >>> t = Tokenizer(Stream)
    >>> t.tokens
    [STMT, MAPPING_VALUE, SEQUENCE_OPEN, STMT, SEQEUNCE_SEPARATOR, STMT, SEQEUNCE_SEPARATOR, STMT, SEQUENCE_CLOSE]
    """

    def __init__(self, stream, indent_size=2):
        """
        Initialise a tokenizer with a list of string. the :param:indent_size if not defined is 2
        """
        self.stream = stream
        self.indent_size = indent_size
        self.colIdx = -1
        self.tokens = []
        self.tokenize()  # call tokenize function

    def tokenize(self):
        """
        Iterate through all the characters in the file and find the boundaries
        ---
        """
        colIdx = self.colIdx + 1
        # totalcount = tokenizer.totalcount
        tokens = self.tokens
        stream = self.stream

        for lineIdx, line in enumerate(stream):
            # iterate through each line of the file
            pointer = 0
            # print(line) # DEBUG

            if line[-1:] != '\n':
                raise TokenizerError(lineIdx, '-1', 'No end of line found')
            else:
                line = line[:-1]  # remove the end of line!

            # ---------------------------------------------------------------
            #   Find INDENNT:
            #   ---
            #   Example
            #   """
            #   >>> string = 'a line without any ident'
            #   >>> indents = re.split(r'^  ', string')
            #   ['a line without any indent']
            #   >>> string = '    two indents in this line'
            #   >>> len(re.split(r'^  ', string)) == 2
            #   True
            #   """
            # ---------------------------------------------------------------
            indent_pattern = '^ {'+ str(self.indent_size) +'}' # use regex to find the indent based on the user defined indent_size
            indents = re.split(indent_pattern, line)
            depth = -1
            while len(indents) > 1:
                depth += 1
                self.tokens.append(
                    Token('  ', lineIdx, depth * self.indent_size, 'INDENT'))
                line = line[self.indent_size:]  # shorten the line by removing the indent
                pointer += self.indent_size
                indents = re.split(indent_pattern, line)

            # if there are more things to be tokenised, check if whitespaces are well-defined
            if len(line) and line[0] == ' ':
                raise TokenizerError(lineIdx, pointer, 'The indent size is {}, but additional whitespaces are found'.format(self.indent_size))


            # ---------------------------------------------------------------
            #   COMMENT CHECKER:
            #    Take the nearest # found and truncate the sentence by reducing #    the line
            # ---------------------------------------------------------------
            comment_idx = line.find('#')
            if comment_idx != -1:  # check if there's a comment in the line, return the first '#' found
                # if there is a comment, shorten the line until the point where
                # the comment starts
                line = line[:comment_idx]
            line = line.rstrip()  # remove trailing whitespaces at the back

            # ---------------------------------------------------------------
            #   TOKENIZE the rest of the stuff
            # ---------------------------------------------------------------
            split_bywhite = line.split(' ')
            for idx, toks in enumerate(split_bywhite):

                # if len(toks) == 0: # random white space found
                #     raise TokenizerError(lineIdx, pointer, 'more than one white space used {}'.format(toks))

                if toks == ':':
                    self.tokens.append(
                        Token(toks, lineIdx, pointer, 'MAPPING_VALUE'))
                elif toks == '[':
                    self.tokens.append(
                        Token(toks, lineIdx, pointer, 'SEQUENCE_OPEN'))
                elif toks == ']':
                    self.tokens.append(
                        Token(toks, lineIdx, pointer, 'SEQUENCE_CLOSE'))
                elif toks == ',':
                    self.tokens.append(
                        Token(toks, lineIdx, pointer, 'SEQEUNCE_SEPARATOR'))
                elif len(toks) > 0:
                    self.tokens.append(Token(toks, lineIdx, pointer, 'STMT'))

                # add one for each whitespace stripped
                pointer += len(toks) + 1


# ---------------------------------------------------------------------------
class Token(object):
    """
    A tokenizer convert the character into tokens. The :class: Token describes the attributes of each Token.

    :param: c : the character or word itself
    :param: lineIdx : the line number where c is found
    :param: colIdx : the character number of the lineIdx
    :param: tok_type : the type of token, either `STMT`, `MAPPING_VALUE`, `SEQEUNCE_SEPARATOR`, `SEQUENCE_OPEN`, `SEQUENCE_CLOSE` and `INDENT`
    """

    def __init__(self, c, lineIdx, colIdx, tok_type):
        """
        initialised the character

        -----
        :param c : a single character
        :param lineIdx : the line number of the file
        :param colIdx : the column number of the file
        :parm sourceID : if multiple files are given in the :argument, this corresponds to the nth file.
        """
        accepted_tokens = ['STMT',
                           'MAPPING_VALUE',
                           'SEQEUNCE_SEPARATOR',
                           'SEQUENCE_OPEN',
                           'SEQUENCE_CLOSE',
                           'INDENT']
        self.c = c
        self.lineIdx = lineIdx
        self.colIdx = colIdx
        if tok_type in accepted_tokens:  # check that i have input an allowed token type
            self.tok_type = tok_type
        else:
            TokenizerError(lineIdx, colIdx,
                           'Irrelevant token type given {}'.format(tok_type))
        # print('Token at {}, {}\t= {}'.format(lineIdx, colIdx, c)) # DEBUG

    def output(self):
        return (str(self.lineIdx) + ' ' + str(self.colIdx) +
                ' ' + self.type + ' ' + str(self.c) + '\n')

    def __str__(self):  # same as output
        return (str(self.c))

    def __repr__(self):
        return str(self.tok_type)

    def __eq__(self, other):
        return self.__str__() == other

    def __hash__(self):
        # since the line and col indices are unique, we can use it as a hash
        # code.
        return hash(str(self.lineIdx) + str(self.colIdx))


# -----------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------

if __name__ == '__main__':
    import doctest
    print('Starting doctest!')
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
