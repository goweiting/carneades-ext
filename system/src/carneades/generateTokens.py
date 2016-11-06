import string

_special_tokens = {
    #  grouped in order or frequency
    'SPACE': ' ',
    'SEQUENCE_ENTRY': '-',
    'MAPPING_VALUE': ':',
    'LITERAL_BLOCK': '|',
    'COMMENT': '#',
    'POLARITY_SIGN': '~'
}

_ALPHA_DIGITS = string.ascii_letters + string.digits  # other characters allowed
_special_list = _special_tokens.values()  # a list of values, for easy search

pointer = -1  # the token we are currently lexing
lineIdx = -1
colIdx = -1

class tokenizer(object):
    """
    Takes in a stream of character and tokenize them according to the rule
    """

    def __init__(self, stream, indent_size):
        self.stream = stream
        self.indent_size = indent_size
        self.indent_stack = []
        self.totalcount = sum([len(stream[i]) for i in range(0,len(stream))]);
        self.tokens = []; # tokens from the stream

    def tokenize(self):
        """
        Iterate through all the characters in the file and find the boundaries
        """
        global pointer, lineIdx, colIdx

        while pointer < self.totalcount: # iterate through all the character until the end of the source
            pointer += 1;
            colIdx += 1;
            lineBoundary = len(self.stream[lineIdx])

            line = lines[lineIdx];
            if line.find('#'): # check if there's a comment in the line
                self.lineBoundary =  line.find('#')

            while self.colIdx < self.lineBoundary: # iterate through the line
                c = self.lines[self.lineIdx][self.colIdx] #
                # ignore comments:
                while c != '#': # a comment must end with a new line
                    # find boundary using longest matching rule to tokenise!
                    (token, self.colIdx) = longest_matching(c)

                # if comment found, fast foward the pointer to end of line:

    def lookahead(self, stepsize=1):
        """
        Return the next element from the currentIdx, as long as it is within the lineBoundary
        """
        next_colIdx = self.colIdx + stepsize;
        if next_colIdx < self.lineBoundary: # check if the next character is overflowing
            return self.lines[lineIdx][next_colIdx]
        else:
            raise NewLineError('NewLine Expected But Not Found at ...')


    def longest_matching(self, c):
        """
        use the longest matching rule to find the word boundary,
        returns :class: token with boundary index
        """
        if c in special_list:
            if c == '~': # polarity switch
                token = token(c, lineIdx, colIdx, 'POLARITY_SIGN');

            # elif c == ' ': # SPACE
            # elif c == '-': # SEQUENCE_ENTRY
            # elif c == ':': # MAPPING_VALUE





class token(object):
    """
    A tokenizer convert the character into tokens
    """

    def __init__(self, c, lineIdx, colIdx):
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
        self.type = None

        if c in special_list:  # add the token type into the tokens
            if c == '\n':
                self.c = ''  # replace it to prevent it from writing newline
                self.type = 'PADDING_NEWLINE'
            else:
                for tok_type, val in special_char.items():
                    if val == c:
                        self.type = tok_type
        else:
            self.type = 'CHARACTER_DIGITS'

    def output(self):
        return (str(self.lineIdx) + ' ' + str(self.colIdx) +
                ' ' + self.type + ' ' + str(self.c) + '\n')

    def __str__(self):  # same as output
        return self.output()
