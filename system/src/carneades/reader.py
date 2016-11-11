# Reader class that encapsulated the scanner, lexer and parser.
# It takes in a ``.yml`` file containing the propositions and arguments
# then, generates the argumentation graph using the CAES
# ---------------------------------------------------------------------------
import logging

from caes import *
from tokenizer import Tokenizer
from parser import Parser, Node
from error import ReaderError

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
DOCTEST = True

if __name__ == '__main__':
    """
    the main function that processes the file(s) passed into the command line:
    Usage: $ python carneades/reader.py [file(s)/directory]
    """
    # if DOCTEST:
    import doctest
    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
    # else:
    # import os
    # import sys
    #     filenames = sys.argv[1:]
    #     num_files = len(filenames)
    #
    #     cwd = os.getcwd()
    #
    #     r = Reader()
    #     r.load(filenames[0])

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
