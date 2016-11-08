import re
from error import *


class tokenizer(object):
    """
    Takes in a stream of character and tokenize them according to the rule
    ---
    DOCTEST:
    Every stream is just a list of one str for modularised testing
    >>> stream = ['Hello World# IGNORE MY COMMENT ! ##\\n', ':\\n', '\\n']
    >>> t = tokenizer(stream)
    >>> t.tokenize();
    >>> t.tokens
    [STMT, STMT, MAPPING_VALUE]

    Ill form (no End of line)
    >>> stream = ['A sequence : ', '  - An indent expected here!']
    >>> try:
    ...     t = tokenizer(stream).tokenize()
    ... except TokenizerError:
    ...     pass


    Indent detector
    >>> stream = ['A sequence : \\n', '  An indent expected here!\\n', '    nested indents\\n']
    >>> t = tokenizer(stream); t.tokenize()
    >>> t.tokens
    [STMT, STMT, MAPPING_VALUE, INDENT, STMT, STMT, STMT, STMT, INDENT, INDENT, STMT, STMT]

    Sequence separator:
    >>> Stream = ["ASSUMPTION : [ ONE , TWO , THREE ]\\n"]
    >>> t = tokenizer(Stream); t.tokenize()
    >>> t.tokens

    >>> stream = open('../../samples/test_lexer.yml').readlines();
    >>> t = tokenizer(stream)
    >>> t.tokenize()
    >>> t.tokens
    """

    def __init__(self, stream):
        self.stream = stream
        # self.indent_size = indent_size
        self.indent_stack = []
        self.colIdx = -1
        self.tokens = []

    def tokenize(self):
        """
        Iterate through all the characters in the file and find the boundaries
        ---
        """
        colIdx = self.colIdx + 1
        # totalcount = tokenizer.totalcount
        tokens = self.tokens
        stream = self.stream

        for lineIdx in range(0, len(stream)):
            # iterate through all the character until the end of the source
            line = stream[lineIdx]
            pointer = 0
            # print(line) # DEBUG

            if line[-1:] != '\n':
                raise TokenizerError(lineIdx, '-1', 'No end of line found')
            else:
                line = line[:-1]  # remove the end of line!

            # ---------------------------------------------------------------
            #   Find INDENNT:
            # ---------------------------------------------------------------
            indents = re.split(r'^  ', line)
            depth = -1
            while len(indents) > 1:
                depth += 1
                self.tokens.append(Token('  ', lineIdx, depth * 2, 'INDENT'))
                line = line[2:]  # shorten the line
                pointer += 2
                indents = re.split(r'^  ', line)

            # print(line) # DEBUG

            # ---------------------------------------------------------------
            #   COMMENT CHECKER:
            #    Take the nearest # found and truncate the sentence by reducing #    the lineBoundary
            # ---------------------------------------------------------------
            comment_idx = line.find('#')
            if comment_idx != -1:  # check if there's a comment in the line, return the first '#' found
                # lineBoundary = comment_idx # and set the lineBoundary if
                # there is
                # remove trailing whitespace on the right too
                line = line[:comment_idx]

            # ---------------------------------------------------------------
            #   TOKENIZE the rest of the stuff
            # ---------------------------------------------------------------
            line = line.rstrip()
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


class Token(object):
    """
    A tokenizer convert the character into tokens
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
        self.c = c
        self.lineIdx = lineIdx
        self.colIdx = colIdx
        self.tok_type = tok_type
        # print('Token at {}, {}\t= {}'.format(lineIdx, colIdx, c)) # DEBUG

    def output(self):
        return (str(self.lineIdx) + ' ' + str(self.colIdx) +
                ' ' + self.type + ' ' + str(self.c) + '\n')

    def __str__(self):  # same as output
        return (str(self.c))

    def __repr__(self):
        return (str(self.tok_type))


# -----------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------

if __name__ == '__main__':
    # do doctest here!
    import doctest
    # import carneades
    print('Starting doctest!')
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
