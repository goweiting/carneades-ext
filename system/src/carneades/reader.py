# Reader class that encapsulated the scanner, lexer and parser.
# It takes in a ``.yml`` file (may support more than one in future) and
# generates the json file which can be used by the caes to create the
# argumentation graph.

__all__ = ['Reader']

import os
import sys
import logging

special_char = {
#  grouped in order or frequency
'PADDING_SPACE'               : ' ',
'PADDING_TAB'                 : '\t',
'PADDING_NEWLINE'             : '\n',
'INDICATOR_SEQUENCE_ENTRY'    : '-',
'INDICATOR_MAP'               : ':',
'INDICATOR_SEQUENCE_START'    : '[',
'INDICATOR_SEQUENCE_END'      : ']',
'INDICATOR_BLOCK'             : '|',
'COMMENT_START'               : '#',
}

special_list = special_char.values();


class Reader(object):
    """
    Reader class encapsulates the processing of the file using the load function
    """
    buffer_size = 4096; # default to 4086, unless user define otherwise


    def __init__(self, buffer_size=4096):
        self.buffer_size = buffer_size  # if defined, set buffer_size
        self.lineIdx = -1;
        self.colIdx  = -1;

    def load(self, path_to_file):
        """
        load the file using the open
        -----
        :param path_to_file : the path to the file to be opened

        """

        # Scanning and lexing
        print('\tTokenizing file...');
        s = '{}.tok'.format(path_to_file);
        with open(s, 'w') as w:
            with open(path_to_file, 'r', buffering=self.buffer_size) as f:
                self.tokenize(f, w) # tokenise the file
        f.close();
        w.close();
        print('\tdone')

        # Parsing:
        print('\tParsing tokens...')


    def tokenize(self, f, w):
        """
        Iterate through all the characters in the file and find the boundaries
        """
        # global colIdx, lineIdx;

        for line in f: # read each line
            self.lineIdx += 1;
            for c in line: # iterate through each c
                self.colIdx += 1;
                # print(c, self.lineIdx, self.colIdx) # DEBUG

                # parse the stream according to the syntax devised:
                # Find the word boundaries and special characters:
                tok_c = token(c, self.lineIdx, self.colIdx);
                w.write(tok_c.output());


class token(object):
    """
    A tokenizer convert the character into tokens
    """

    #  ':' - a map mapping a key to value or start of a sequence
    #  '-' - an item in the a sequence
    #  '|' - the following lines are values of the nearest key
    # '#' - denote the start of a comment
    # '[', ']' - boundary of a sequence

    def __init__(self, c, lineIdx, colIdx):
        """
        initialised the character

        -----
        :param c : a single character
        :param lineIdx : the line number of the file
        :param colIdx : the column number of the file
        :parm sourceID : if multiple files are given in the argument, this corresponds to the nth file.
        """
        self.c = c
        self.lineIdx = lineIdx
        self.colIdx = colIdx
        self.type = None;

        if c in special_list: # add the token type into the tokens
            if c == '\n':
                self.c = '' # replace it to prevent it from writing newline
                self.type = 'PADDING_NEWLINE';
            else:
                for tok_type, val in special_char.items():
                    if val == c:
                        self.type = tok_type;
        else:
            self.type = 'SYMBOL'

    def output(self):
        return (str(self.lineIdx) + ' ' + str(self.colIdx) +
        ' ' + self.type + ' ' + str(self.c) + '\n')

    def __str__(self): # same as output
        return self.output();


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    """
    the main function that processes the file(s) passed into the command line:
    Usage: $ python carneades/reader.py [file(s)/directory]
    """
    filenames = sys.argv[1:]
    num_files = len(filenames)

    cwd = os.getcwd();

    r = Reader();
    r.load(filenames[0])


    # if filenames == []:  # no argument passed into the command line
    #     print('\tERROR: No filename detected!\n\n')
    #
    # elif len(filenames) > 1:  # if use gave a list of filenames
    #     # inform the number of files
    #     print('\t', num_files, ' file(s) detected\n')
    #     for filename in filenames:
    #         print(filename)
    #         reader = Reader()
    #         with open(filename) as f:
    #             reader.load(f)
    #
    # else:  # Support if user gives a directory instead of a list of filename
    #     try:
    #         open(filenames[0])  # check if it is a directory
    #     except IsADirectoryError:
    #         path = os.path.join(os.getcwd(), filenames[0])
    #         print('\tEntering directory:\n\t', path)
    #         os.chdir(path)
    #         filenames = os.listdir()  # get a list of files
    #         num_files = len(filenames)
    #         # inform the number of files
    #         print('\t', num_files, ' file(s) detected\n')
    #
    #         for filename in filenames:
    #             print('\t', filename)
    #             reader = Reader()
    #             with open(filename) as f:
    #                 reader.load(f)
