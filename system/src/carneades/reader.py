# Reader class that encapsulated the scanner, lexer and parser.
# It takes in a ``.yml`` file containing the propositions and arguments
# then, generates the argumentation graph using the CAES
# ---------------------------------------------------------------------------
import logging

from carneades.caes import *
from carneades.tokenizer import Tokenizer
from carneades.parser import Parser, Node
from carneades.error import ReaderError

LOGLEVEL = logging.INFO
logging.basicConfig(format='%(levelname)s: %(message)s', level=LOGLEVEL)


# ---------------------------------------------------------------------------
class Reader(object):
    """
    Reader class encapsulates the processing of the file using the load function
    ---
    DOCTEST:
    >>> reader = Reader(); # use default buffer_size
    >>> reader.load('../../samples/template.yml')
    >>>
    """
    buffer_size = 4096  # default to 4086, unless user define otherwise
    # indent_size = 2

    def __init__(self, buffer_size=4096, indent_size=2):
        """
        Initialise the Reader to read your source file with the user's settings
        ----
        PARAMETER:
        :param:buffer_size, default to 4096
        :param:indent_size, default to 2
        """
        self.buffer_size = buffer_size
        self.indent_size = indent_size

    def load(self, path_to_file):
        """
        load the file of interest, tokenize and parse it. Using the information given by the user in the file(s), call CAES to evaluate the arguments
        -----
        :param path_to_file : the path to the file to be opened

        """
        # ---------------------------------------------------------------
        #   Scanning and lexical analsys
        # ---------------------------------------------------------------
        logging.info('\tTokenizing file...')
        # read the file and store it as a list of lines!
        stream = open(path_to_file, 'r',
                      buffering=self.buffer_size).readlines()
        # call tokenizer will call tokenize() when initialised
        t = Tokenizer(stream, self.indent_size)
        toks = t.tokens
        # print(stream_tokens) # DEBUG
        logging.info('\t\t\tdone')

        # ---------------------------------------------------------------
        #   Parsing:
        # ---------------------------------------------------------------
        logging.info('\tParsing tokens...')

        # parse() will be initiated automatically once initialised
        p = Parser(toks)
        # retrieve the nodes from parser:
        proposition = p.proposition
        argument = p.argument
        assumption = p.assumption
        parameter = p.parameter

        logging.info('\t\t\tdone')

        # ---------------------------------------------------------------
        #   Translate it into data structure for CAES
        # ---------------------------------------------------------------

        # Processing proposition:
        logging.info('\tAdding propositions to CAES')
        caes_propliteral = dict()
        for p in proposition.children:  # iterate through the list of children
            prop_id = p.data
            text = p.children[0].data
            # rename the PROP_ID in case of long names
            # here, added prop_id as a field in PropLierals!
            caes_propliteral[prop_id] = PropLiteral(
                text)  # True by defailt

        # -----------------------------------------------------------------
        logging.info('\tAdding assumptions to CAES')
        caes_assumption = set()
        tmp = assumption.children  # the list of assumptions
        assert type(tmp) is list

        for assume in tmp:
            assert type(assume) is str
            # check that the assumptions are in the set of caes_propliteral
            if check_prop(caes_propliteral, assume):

                if assume[0] == '-':  # switch the polarity of the outcome!
                    prop = caes_propliteral[assume[1:]]
                    prop = prop.negate()
                else:
                    prop = caes_propliteral[assume]

            else:
                raise ReaderError(
                    'No such literal {} found in the propsitions defined above'.format(assume))

            caes_assumption.add(prop)

        # -----------------------------------------------------------------
        logging.info('\tAdding arguments to CAES')
        # In caes: an argument consists of the following fields:
        # conclusion
        # premises
        # exceptions
        # For proofstandards, it is a list of pairs consisting of proposition
        # and proof standard
        caes_arguments = dict()  # a dictionary to hold the arguments
        caes_proofstandard = dict()
        for arg_id in argument.children:
            # iterating through the each node of argument
            assert type(arg_id) is Node  # typecheck

            premise = set(arg_id.find_child('premise').children)
            exception = set(arg_id.find_child('exception').children)
            proofstandard = arg_id.find_child('proofstandard').children[0].data
            weight = float(arg_id.find_child('weight').children[0].data)
            conclusion = arg_id.find_child('conclusion').children[0].data

            # check the weight
            if weight < 0 or weight > 1:
                raise ReaderError(
                    'weight for {} ({}) is not in range [0,1]'.format(arg_id, weight))

            # check that the literals are valid:
            ok = check_prop(caes_propliteral, conclusion) and \
                check_proofstandard(proofstandard) and \
                check_prop(premise) and \
                check_prop(exception)

            if ok:
                caes_arguments[arg_id] = Argument(
                    conclusion=conclusion, premises=premise, exceptions=exception)
                caes_proofstandard[arg_id] = proofstandard
            else:
                raise ReaderError(
                    '{}\'s propositions are invalid'.format(arg_id))

        # -----------------------------------------------------------------
        logging.info('\tAdding parameter to CAES')
        caes_alpha = 0
        caes_beta = 0
        caes_gamma = 0
        for p in parameter.children:
            assert type(p) is Node  # these are nodes!

            if p.data == 'alpha':
                caes_alpha = p.children[0].data
                # check that they are within range
                if caes_alpha > 1 or caes_alpha < 0:
                    raise SyntaxError(
                        'caes_alpha must be within the range of 0 and 1 inclusive. {} given'.format(caes_alpha))

            elif p.data == 'beta':
                caes_beta = p.children[0].data
                if caes_beta > 1 or caes_beta < 0:
                    raise SyntaxError(
                        'caes_beta must be within the range of 0 and 1 inclusive. {} given'.format(caes_beta))

            elif p.data == 'gamma':
                caes_gamma = p.children[0].data
                if caes_gamma > 1 or caes_gamma < 0:
                    raise SyntaxError(
                        'caes_gamma must be within the range of 0 and 1 inclusive. {} given'.format(caes_gamma))


# -----------------------------------------------------------------------------
#       Additional Functions to help check the propositions
# -----------------------------------------------------------------------------
def check_prop(caes_propliteral, prop_id):
    """
    given the dictionary of caes_propliteral, check if a propliteral with prop_id exists
    If :param: prop_id is a set of strings, iteratively call check_prop on each element in the set.

    :rtype: bool
    """
    if type(prop_id) is set:
        props = list(prop_id)
        checker = True
        for p in props:
            checker = checker and check_prop(caes_propliteral, p)
        return checker
    elif type(prop_id) is str:
        if prop_id[0] == '-':
            prop_id = prop_id[1:]

        if prop_id in caes_propliteral.keys():
            return True
        else:
            return False


def check_proofstandard(query):
    """
    check if the proofstandard user input is a valid input.
    Return the CAES's version of the similar proofstandard
    """
    standards = {'scintilla': "scintilla",
                 'preponderance': "preponderance",
                 'clear and convincing': "clear_and_convincing",
                 'beyond reasonable doubt': "beyond_reasonable_doubt",
                 'dialectical validitys': "dialectical_validity"}

    if query in standards.keys():
        return standards[query]
    else:
        raise ReaderError('Invalid proof standard {} found'.format(query))


def check_range(lower, higher, query):
    """
    check if query falls in the range of higher and lower
    """
    if query > higher or query < lower:
        return False
    else:
        return True

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
