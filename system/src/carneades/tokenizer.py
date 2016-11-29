import re
from collections import deque
from error import TokenizerError


# ---------------------------------------------------------------------------
class Tokenizer(object):
    """
    Takes in a stream of character and tokenize them according to the rule
    ---
    Check that comments are removed:
    Every stream is just a list of one str for modularised testing
    >>> stream = ['Hello World :# IGNORE MY COMMENT ! ##\\n', '\\n']
    >>> t = Tokenizer(stream)
    >>> t.tokens
    [STMT, STMT, MAPPING_VALUE]

    Indent detector
    >>> stream = ['hey: you, are okayy? \\n', '  An indent expected here ,\\n', '    nested indents\\n']
    >>> t = Tokenizer(stream) # use default indent_size = 2
    >>> t.tokens
    [STMT, MAPPING_VALUE, STMT, STMT, STMT, INDENT, STMT, STMT, STMT, STMT, STMT, INDENT, INDENT, STMT, STMT]

    >>> stream = ['   Testing with 3 spaces as indent\\n']
    >>> try : t = Tokenizer(stream)
    ... except TokenizerError: pass
    >>> t = Tokenizer(stream, 3)
    >>> t.tokens
    [INDENT, STMT, STMT, STMT, STMT, STMT, STMT]

    Sequence separator:
    >>> Stream = ["ASSUMPTION:[ONE, TWO, THREE ]\\n"]
    >>> T = Tokenizer(Stream)
    >>> T.tokens
    [STMT, MAPPING_VALUE, SEQUENCE_OPEN, STMT, SEQUENCE_SEPARATOR, STMT, SEQUENCE_SEPARATOR, STMT, SEQUENCE_CLOSE]

    >>> stream = ['ASSUMPTION : [ one, two, three only ]\\n']
    >>> T = Tokenizer(stream)
    >>> T.tokens
    [STMT, MAPPING_VALUE, SEQUENCE_OPEN, STMT, SEQUENCE_SEPARATOR, STMT, SEQUENCE_SEPARATOR, STMT, STMT, SEQUENCE_CLOSE]

    Added support for not having to separate it by spaces:
    >>> stream = ['ACCEPTABILITY:[one,two,three only]\\n']
    >>> t=Tokenizer(stream)
    >>> t.tokens
    [STMT, MAPPING_VALUE, SEQUENCE_OPEN, STMT, SEQUENCE_SEPARATOR, STMT, SEQUENCE_SEPARATOR, STMT, STMT, SEQUENCE_CLOSE]

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
        Iterate through all the characters in the file and find the tokens
        ---
        """
        colIdx = self.colIdx + 1
        # totalcount = tokenizer.totalcount
        tokens = self.tokens
        stream = self.stream

        for lineIdx, line in enumerate(stream):
            # iterate through each line of the file
            lineIdx += 1 # starts from 1 instead of 0
            pointer = 0

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
            # use regex to find the indent based on the user defined
            # indent_size
            indent_pattern = '^ {' + str(self.indent_size) + '}'
            indent = ' '
            indents = re.split(indent_pattern, line)
            depth = -1
            while len(indents) > 1:
                depth += 1
                self.tokens.append(
                    Token('  ', lineIdx, depth * self.indent_size, 'INDENT'))
                # shorten the line by removing the indent
                line = line[self.indent_size:]
                pointer += self.indent_size
                indents = re.split(indent_pattern, line) # get the next indent

            # if there are more things to be tokenised, check if whitespaces
            # are well-defined
            if len(line) and line[0] == ' ':
                raise TokenizerError(
                    lineIdx, pointer, 'The indent size is {}, but additional whitespace is found'.format(self.indent_size))

            # ---------------------------------------------------------------
            #   COMMENT CHECKER:
            #    Take the nearest # found and truncate the sentence by reducing #    the line
            # ---------------------------------------------------------------
            comment_idx = line.find('#')
            if comment_idx != -1:
                # if there is a comment, shorten the line until the point where
                # the comment starts, hence ignoring the comments
                line = line[:comment_idx]

            line = line.rstrip()  # remove trailing whitespaces at the back

            # ---------------------------------------------------------------
            #   TOKENIZE the rest of the stuff
            # ---------------------------------------------------------------
            while len(line):
                pointer += 1
                char = line[0]

                if char == ':':
                    self.tokens.append(
                        Token(char, lineIdx, pointer, 'MAPPING_VALUE'))
                    line = line[1:]
                    continue

                elif char == '[':
                    line, pointer = self.tokenize_seq(line, lineIdx, pointer-1) # trigger to find the sequnce
                    continue

                elif char == ' ':
                    line = line[1:] # ignore the white spaces
                    continue

                else:  # word
                    # anything as long as it is not a character found above
                    pattern = r'^[^ :\[]+'
                    word = re.findall(pattern, line)[0]
                    self.tokens.append(Token(word, lineIdx, pointer, 'STMT'))
                    line = line[len(word):]
                    pointer += len(word) - 1
                    continue

    def tokenize_seq(self, line, lineIdx, pointer):
        """
        Given a line, find the remaining sequence and tokenize them
        Also, check that the syntax for tokens is well-respected
        With this, usage of commas is okay as long as it is not in the sequence separator
        """
        assert len(line) != 0
        assert type(line) == str

        while len(line):
            pointer += 1
            char = line[0]

            if char == '[':
                self.tokens.append(
                    Token(char, lineIdx, pointer, 'SEQUENCE_OPEN'))
                line = line[1:]
                continue

            elif char == ']':
                self.tokens.append(
                    Token(char, lineIdx, pointer, 'SEQUENCE_CLOSE'))
                line = line[1:]
                print(line)
                return line, pointer # complete sequence, return to the caller

            elif char == ',':
                self.tokens.append(
                    Token(char, lineIdx, pointer, 'SEQUENCE_SEPARATOR'))
                line = line[1:]
                continue

            elif char == ' ':
                line = line[1:] # ignore the white spaces
                continue

            else:
                # anything as long as it is not a character found above
                pattern = r'^[^ ,:\[\]]+'
                word = re.findall(pattern, line)[0]
                self.tokens.append(Token(word, lineIdx, pointer, 'STMT'))
                line = line[len(word):]
                pointer += len(word) - 1
                continue

        if len(line) == 0:
            raise TokenizerError(lineIdx, pointer, '[ found but is not closed with ]')

# ---------------------------------------------------------------------------
class Token(object):
    """
    A tokenizer convert the character into tokens. The :class: Token describes the attributes of each Token.

    :param: c : the character or word itself
    :param: lineIdx : the line number where c is found
    :param: colIdx : the character number of the lineIdx
    :param: tok_type : the type of token, either `STMT`, `MAPPING_VALUE`, `SEQUENCE_SEPARATOR`, `SEQUENCE_OPEN`, `SEQUENCE_CLOSE` and `INDENT`
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
                           'SEQUENCE_SEPARATOR',
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
