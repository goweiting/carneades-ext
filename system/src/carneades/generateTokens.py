import string
import re
from error import *

class tokenizer(object):
    """
    Takes in a stream of character and tokenize them according to the rule
    ---
    DOCTEST:
    Every stream is just a list of one str for modularised testing
    >>> stream = ['# IGNORE MY COMMENT ! ##\\n','~\\n',':\\n']
    >>> t = tokenizer(stream, 2)
    >>> t.tokenize();
    >>> t.tokens
    [POLARITY_SIGN, MAPPING_VALUE]

    ---
    Check syntax - Proper end of line: If no '\\n' found raise error
    >>> t = tokenizer(['w w '], 2)
    >>> try:
    ...     t.tokenize()
    ... except SyntaxError:
    ...         pass

    ---
    Correctly find word boundary in a sentence:
    >>> stream2 = ['a sentence with 5 tokens\\n']
    >>> t2 = tokenizer(stream2, 2);
    >>> t2.tokenize();
    >>> t2.tokens
    [STMT, STMT, STMT, STMT, STMT]

    >>> stream3 = ['A mixute of :\\n','- ~tokens\\n']
    >>> t3 = tokenizer(stream3, 2)
    >>> t3.tokenize();
    >>> t3.tokens
    [STMT, STMT, STMT, MAPPING_VALUE, SEQUENCE_ENTRY, POLARITY_SIGN, STMT]
    """


    special_tokens = {
        #  grouped in order or frequency
        'SPACE': ' ',
        'SEQUENCE_ENTRY': '-',
        'MAPPING_VALUE': ':',
        'LITERAL_BLOCK': '|',
        'COMMENT': '#',
        'POLARITY_SIGN': '~'
    }

    ALPHA_DIGITS = string.ascii_letters + string.digits  # other characters allowed
    special_list = special_tokens.values()  # a list of values, for easy search

    def __init__(self, stream, indent_size):
        self.stream = stream
        self.indent_size = indent_size
        self.indent_stack = []
        self.colIdx = -1
        self.tokens = []

    def tokenize(self):
        """
        Iterate through all the characters in the file and find the boundaries
        ----
        Some testing:
        ----
        .find('#') always returns the smallest #
        >>> line = ['# comment # comment\\n'];
        >>> line[0].find('#')
        0

        """
        colIdx = self.colIdx + 1;
        # totalcount = tokenizer.totalcount
        tokens = self.tokens
        stream = self.stream

        for lineIdx in range(0, len(stream)):
            # iterate through all the character until the end of the source
            line = stream[lineIdx];
            # print(line) # DEBUG

            if line[-1:] != '\n':
                raise SyntaxError('No end of line found')
            else:
                line = line[:-1] # remove the end of line!
                lineBoundary = len(line) # this is local to the function, -1 because the line must end with a new line
                colIdx = 0; # start from the very first character

            # ---------------------------------------------------------------
            #   COMMENT CHECKER:
            #    Take the nearest # found and truncate the sentence by reducing #    the lineBoundary
            # ---------------------------------------------------------------
            if line.find('#') != -1: # check if there's a comment in the line, return the first '#' found
                lineBoundary = line.find('#') # and set the lineBoundary if there is

            # Now, iterate through each column (starting from 0)
            while colIdx < lineBoundary: # iterate through the line
                c = line[colIdx]
                # -----------------------
                #   SINGLE VALUE TOKENS
                # -----------------------
                if c == '~':
                    token = Token(c, lineIdx, colIdx, 'POLARITY_SIGN')

                elif c == ':':
                    token = Token(c, lineIdx, colIdx, 'MAPPING_VALUE')

                elif c == '-':
                    token = Token(c, lineIdx, colIdx, 'SEQUENCE_ENTRY')
                    colIdx += self.indent_size-1; # SEQUENCE_ENTRY takes up 1 space and the rest is the indent

                elif c in tokenizer.ALPHA_DIGITS:
                    # start longest matching rule here!
                    # find the next whitespace and use it as word boundary
                    line_cut = line[colIdx:]
                    space_idx = line_cut.find(' ');
                    endmark = line_cut.find('\n');

                    if space_idx +1: # a space is found:
                        c = line[colIdx : colIdx+space_idx] # slice the word out
                        token = Token(c, lineIdx, colIdx, 'STMT')
                        colIdx += space_idx;

                    else:
                        c = line[colIdx : -1]
                        token = Token(c, lineIdx, colIdx, 'STMT')
                        colIdx = lineBoundary

                    # else:
                    #     TokenizerError(lineIdx, colIdx, 'STMT not bounded by white space!')
                elif c == ' ': # find indents

                # Get ready for the next character
                self.tokens.append(token)
                colIdx += 1;
                # print(colIdx) # DEBUG



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
        self.c          = c
        self.lineIdx    = lineIdx
        self.colIdx     = colIdx
        self.tok_type   = tok_type
        # print('Token at {}, {} = {}'.format(lineIdx, colIdx, c)) # DEBUG

    def output(self):
        return (str(self.lineIdx) + ' ' + str(self.colIdx) +
                ' ' + self.type + ' ' + str(self.c) + '\n')

    def __str__(self):  # same as output
        return (str(self.tok_type))

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
