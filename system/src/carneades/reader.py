# Reader class that encapsulated the scanner, lexer and parser.
# It takes in a ``.yml`` file containing the propositions and arguments
# then, generates the argumentation graph using the CAES
# ---------------------------------------------------------------------------
import logging

from caes import *
from tokenizer import Tokenizer
from parser import Parser, Node
from error import ReaderError

LOGLEVEL = logging.DEBUG
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

        # ---------------------------------------------------------------
        #   Parsing:
        # ---------------------------------------------------------------
        logging.info('\tParsing tokens...')

        # parse() will be initiated automatically once initialised
        p = Parser(toks)

        # ---------------------------------------------------------------
        #   Translate it into data structure for CAES
        # ---------------------------------------------------------------
        caes_propliteral = dict()
        caes_assumption = set()
        caes_arguments = dict()
        caes_proofstandard = dict()
        caes_alpha = float()
        caes_beta = float()
        caes_gamma = float()

        # Processing proposition:
        logging.info('\tAdding propositions to CAES')
        for proplit in p.proposition.children:  # iterate through the list of children
            assert type(proplit) is Node
            prop_id = proplit.data
            text = proplit.children[0].data
            if prop_id[0] == '-':
                raise ReaderError(
                    '- found in {}. Name of propositions are assumed to be True, and no polarity sign is need!'.format(p))
            # rename the PROP_ID in case of long names
            # here, added prop_id as a field in PropLierals!
            # polarity is set to True by defailt
            caes_propliteral[prop_id] = PropLiteral(text)

        # -----------------------------------------------------------------
        logging.info('\tAdding assumptions to CAES')
        tmp = p.assumption.children  # the list of assumptions

        for prop in tmp:
            # check that the assumptions are in the set of caes_propliteral
            if check_prop(caes_propliteral, prop):
                if prop[0] == '-':  # switch the polarity of the outcome!
                    # find the PropLiteral in the dictionary
                    prop = caes_propliteral[prop[1:]]
                    prop = prop.negate()
                else:
                    prop = caes_propliteral[prop]

            caes_assumption.add(prop)
            # logging.info(type(prop))

        # -----------------------------------------------------------------
        logging.info('\tAdding arguments to CAES')
        # In caes: an argument consists of the following fields:
        # conclusion
        # premises
        # exceptions
        # For proofstandards, it is a list of pairs consisting of proposition
        # and proof standard
        for arg_id in p.argument.children:
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
            ok_c, conclusion = check_prop(caes_propliteral, conclusion)
            ok_e, exception = check_prop(caes_propliteral, exception)
            ok_p, premise = check_prop(caes_propliteral, premise)
            ok_ps, proofstandard = check_proofstandard(proofstandard)

            if ok_c and ok_e and ok_p and ok_ps:
                caes_proofstandard[arg_id] = proofstandard
                caes_arguments[arg_id] = Argument(conclusion=conclusion,
                                                  premises=premise, exceptions=exception)
        # -----------------------------------------------------------------
        logging.info('\tAdding parameter to CAES')

        for param in p.parameter.children:
            if param.data == 'alpha':
                caes_alpha = float(param.children[0].data)
                # check that they are within range
                if caes_alpha > 1 or caes_alpha < 0:
                    raise SyntaxError(
                        'caes_alpha must be within the range of 0 and 1 inclusive. {} given'.format(caes_alpha))

            elif param.data == 'beta':
                caes_beta = float(param.children[0].data)
                if caes_beta > 1 or caes_beta < 0:
                    raise SyntaxError(
                        'caes_beta must be within the range of 0 and 1 inclusive. {} given'.format(caes_beta))

            elif param.data == 'gamma':
                caes_gamma = float(param.children[0].data)
                if caes_gamma > 1 or caes_gamma < 0:
                    raise SyntaxError(
                        'caes_gamma must be within the range of 0 and 1 inclusive. {} given'.format(caes_gamma))

        logging.debug('alpha:{}, beta:{}, gamme:{}'.format(
        caes_alpha, caes_beta, caes_gamma))
        logging.debug('propliterals: {} '.format(caes_propliteral))
        logging.debug('arguments: {} '.format(caes_arguments))
        logging.debug('assumptions: {} '.format(caes_assumption))
        logging.debug('arguments {} :'.format(caes_arguments))


        # -----------------------------------------------------------------
        #       draw the argument graph:
        # -----------------------------------------------------------------

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
