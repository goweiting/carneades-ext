import string


class tokenizer(object):
    """
    Takes in a stream of character and tokenize them according to the rule
    ---
    DOCTEST:
    Every stream is just a list of one str for modularised testing
    >>> stream = ['# IGNORE MY COMMENT ! ##\\n', \
                    '~\\n',\
                     ':\\n']
    >>> t = tokenizer(stream, 2)
    >>> t.tokenize();
    >>> t.tokens
    [POLARITY_SIGN, MAPPING_VALUE]
    ---

    Correctly find word boundary in a sentence:
    >>> stream2 = ['this is a sentence with 7 tokens\\n',\
                    'only 4 tokens here #RIGHT\\n']
    >>> t2 = tokenizer(stream2, 2);
    >>> t2.tokenize();
    >>> t2.tokens
    [STMT, STMT, STMT, STMT, STMT, STMT, STMT, STMT, STMT, STMT, STMT]
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

    # Class variables
    pointer = -1  # the index we are currently lexing
    lineIdx = -1
    colIdx  = -1
    totalcount = -1;
    tokens = [];

    def __init__(self, stream, indent_size):
        self.stream = stream
        self.indent_size = indent_size
        self.indent_stack = []
        tokenizer.totalcount = sum([len(stream[i]) for i in range(0,len(stream))]); # update the total length

        # reset the value everytime it is called
        tokenizer.pointer = -1;
        tokenizer.lineIdx = -1;
        tokenizer.colIdx = -1;
        tokenizer.tokens = [];

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
        pointer = tokenizer.pointer + 1;
        lineIdx = tokenizer.lineIdx + 1;
        colIdx = tokenizer.colIdx + 1;
        totalcount = tokenizer.totalcount
        tokens = tokenizer.tokens
        stream = self.stream

        while pointer < totalcount: # iterate through all the character until the end of the source
            line = stream[lineIdx];
            print(line)
            lineBoundary = len(line) # this is local to the function, -1 because the line must end with a new line

            # ---------------------
            #   COMMENT CHECKER:
            # ---------------------
            if line.find('#') != -1: # check if there's a comment in the line
                lineBoundary = line.find('#') # and set the lineBoundary if there is

            print('current pointer at ', str(pointer)) # DEBUG
            print('Lineboundary = {}\tlineIdx = {}'.format(lineBoundary, lineIdx)) # DEBUG

            # Now, iterate through each column (starting from 0)
            while colIdx < lineBoundary: # iterate through the line
                c = line[colIdx]
                print(c, colIdx, pointer); # DEBUG

                # -----------------------
                #   SINGLE VALUE TOKENS
                # -----------------------
                token = None
                if c == '~':
                    token = Token(c, lineIdx, colIdx, 'POLARITY_SIGN')
                elif c == ':':
                    token = Token(c, lineIdx, colIdx, 'MAPPING_VALUE')
                elif c == '-':
                    token = Token(c, lineIdx, colIdx, 'SEQUENCE_ENTRY')
                # elif c == ' ':
                #
                elif c in tokenizer.ALPHA_DIGITS: # start longest matching rule here!
                    # find boundary using longest matching rule to tokenise!
                    (token, colIdx) = self.longest_matching(line, lineIdx, colIdx, lineBoundary)


                tokenizer.tokens.append(token)
                colIdx += 1; # increment
                pointer += 1;

            # conditions at end of the line:
            colIdx = 0;
            delta = len(line) - lineBoundary
            pointer += delta
            lineIdx += 1


    def longest_matching(self, line, lineIdx, colIdx, lineBoundary):
        """
        use the longest matching rule to find the word boundary,
        returns :class: token with boundary index
        ------
        :param: c - the current character it is evaluating
        :param: lineBoundary - the limit it should go to
        :param: colIdx
        :return: The token found and the colIdx that it ends at
        :rtype: :class:`token`
        :rtype: colIdx - the new colIdx that longest matching ended with
        """

        if colIdx < lineBoundary:
            # if there are still characters remain in the line:
            # find spaces:
            space_idx = line.find(' ');
            endline_idx = line.find('\n')
            if space_idx + 1:
                c = line[colIdx:space_idx] # slice the word out
                token = Token(c, lineIdx, colIdx, 'STMT')
                next_colIdx = space_idx;
                break;

            elif endline_idx + 1: # end of line case
                c = line[colIdx:endline_idx]
                token = Token(c, lineIdx, colIdx, 'STMT')
                next_colIdx = endline_idx + 1; # sice endline is 2 character long
                break;

        return (token, next_colIdx)

    def next(self, line, colIdx, lineBoundary):
        pass


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
        print('Token at {}, {} = {}'.format(lineIdx, colIdx, c)) # DEBUG

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
