# Reader class that encapsulated the scanner, lexer and parser.
# It takes in a ``.yml`` file (may support more than one in future) and
# generates the json file which can be used by the caes to create the
# argumentation graph.

__all__ = ['Reader']

import os
import sys
import logging

import carneades.generateTokens
import carneades.parser 

class Reader(object):
    """
    Reader class encapsulates the processing of the file using the load function
    """
    buffer_size = 4096  # default to 4086, unless user define otherwise
    indent_size = 2

    def __init__(self, buffer_size=4096, indent_size=2):
        self.buffer_size = buffer_size  # if defined, set buffer_size
        self.indent_size = indent_size  # use can define the indent size for the syntax
        self.lineIdx = -1
        self.colIdx = -1

    def load(self, path_to_file):
        """
        load the file using the open
        -----
        :param path_to_file : the path to the file to be opened

        """

        # Scanning and lexical analsys
        print('\tTokenizing file...')
        s = '{}.tok'.format(path_to_file)

        lines = open(path_to_file, 'r', buffering=self.buffer_size).readlines() # read the file and store it as a list of lines!
        tokens = tokenizer.tokenize(lines);

        print('\tdone')

        # Parsing:
        print('\tParsing tokens...')






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

    cwd = os.getcwd()

    r = Reader()
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
