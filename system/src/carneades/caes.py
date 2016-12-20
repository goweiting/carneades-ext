# Carneades Argument Evaluation Structure
#
# Copyright (C) 2014 Ewan Klein
# Author: Ewan Klein <ewan@inf.ed.ac.uk>
# Based on: https://hackage.haskell.org/package/CarneadesDSL
#
# For license information, see LICENSE

from collections import namedtuple, defaultdict
import logging, os, re, sys
from textwrap import wrap
from igraph import Graph, plot

# fix to ensure that package is loaded properly on system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tracecalls import TraceCalls
from tokenizer import Tokenizer
from parser import Parser, Node
from error import ReaderError

# ========================================================================
#           READER
# ========================================================================


class Reader(object):
    """
    Reader class encapsulates the processing of the file using the load function
    ---
    DOCTEST:
    >>> reader = Reader(); # use default buffer_size
    >>> reader.load('../../samples/caes_org.yml', dialogue=False)
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    ------ "accused committed murder" IS NOT acceptable ------

    >>> r = Reader()
    >>> d_arg = r.load('../../samplesTest/convergentarg.yml', dialogue=True)
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    <BLANKLINE>
    dialogue mode on
    <BLANKLINE>
    ------ "issue" IS NOT acceptable ------
    <BLANKLINE>
    ------ "issue" IS acceptable ------
    <BLANKLINE>
    ------ "issue" IS acceptable ------

    # A very naive argument here just to test the functionality.
    >>> g = d_arg.graph
    >>> vs_claimed = g.vs.select(state='claimed')
    >>> for i in vs_claimed.indices: print(g.vs[i]['prop'])
    issue
    support 2

    # Check that the getter is working
    >>> claimed_args = d_arg.get_arguments_status('claimed')
    >>> for a in claimed_args: print(a)
    [support 2], ~[] => issue
    [premise2], ~[] => support 2

    # Check that the questioned function is working
    >>> d_arg.set_argument_status(g.vs[i]['prop'], 'questioned')
    >>> args = d_arg.get_arguments_status('questioned')
    >>> for a in args: print(a)
    [premise2], ~[] => support 2
    """

    def __init__(self, buffer_size=4096, indent_size=2):
        """
        Initialise the Reader to read your source file with the user's settings
        ----
        PARAMETER:
        :param buffer_size: defaults to 4096
        :param indent_size: defaults to 2
        """
        # ---------------------------------------------------------------
        #   User defined parameters for the source file and parsing
        # ---------------------------------------------------------------
        self.buffer_size = buffer_size
        self.indent_size = indent_size
        # ---------------------------------------------------------------
        #   Translate it into data structure for CAES
        # ---------------------------------------------------------------
        self.caes_propliteral = dict()
        self.caes_assumption = set()
        self.caes_argument = dict()
        self.caes_proofstandard = list()
        self.caes_weight = dict()
        self.caes_alpha = float()
        self.caes_beta = float()
        self.caes_gamma = float()
        self.caes_issue = set()
        self.argset = ArgumentSet()

    def load(self, path_to_file, dialogue):
        """
        load the file of interest, tokenize and parse it. Using the information
        given by the user in the file(s), call CAES to evaluate the arguments
        -----
        :param path_to_file : the path to the file to be opened
        :param dialogue : If `dialogue = False`, the acceptability check be
        shown. Otherwise, if `dialogue = True`, a dialogue version of the
        arguments will be shown. The class:dialogue illustrates the shifting
        BOP between the
        proponent and opponent at each class:stage. At each stage, the best
        argument is put forth so as to attack the claim by the based on the
        party with the burden of proof.
        """

        # ---------------------------------------------------------------
        #   Scanning and lexical analsys
        # ---------------------------------------------------------------
        logging.info('\tTokenizing file...')
        # read the file and store it as a list of lines!
        stream = open(
            path_to_file, 'r', buffering=self.buffer_size).readlines()
        # call tokenizer will call tokenize() when initialised
        t = Tokenizer(stream, self.indent_size)

        # ---------------------------------------------------------------
        #   Parsing:
        # ---------------------------------------------------------------
        logging.info('\tParsing tokens...')
        p = Parser(t.tokens)

        # ---------------------------------------------------------------
        #   Generating the arguments required for CAES
        # ---------------------------------------------------------------
        # Processing proposition:
        logging.info('\tAdding propositions to CAES')
        for proplit in p.proposition.children:  # iterate through the list of children
            assert type(proplit) is Node
            prop_id = proplit.data
            text = proplit.children[0].data
            if prop_id[0] == '-':
                raise ReaderError(
                    '"-" found in {}. Name of propositions are assumed to be True, and no polarity sign is need!'.
                    format(p))
            # here, added prop_id as a field in PropLierals!
            # polarity is set to True by defailt
            self.caes_propliteral[prop_id] = PropLiteral(text)

        # -----------------------------------------------------------------
        logging.info('\tAdding assumptions to CAES')

        for prop in p.assumption.children:
            # check that the assumptions are in the set of caes_propliteral
            if self.check_prop(self.caes_propliteral, prop):
                if prop[0] == '-':  # switch the polarity of the outcome!
                    # find the PropLiteral in the dictionary
                    prop = self.caes_propliteral[prop[1:]]
                    prop = prop.negate()
                else:
                    prop = self.caes_propliteral[prop]

            self.caes_assumption.add(prop)

        # -----------------------------------------------------------------
        logging.info('\tAdding arguments to CAES')
        # In CAES: an argument consists of the following fields:
        # premises, exceptions, conclusion, weight
        for arg_id in p.argument.children:
            # iterating through the each node of argument
            assert type(arg_id) is Node  # typecheck

            premise = set(arg_id.find_child('premise').children)
            exception = set(arg_id.find_child('exception').children)
            try:
                conclusion = arg_id.find_child('conclusion').children[0].data
                weight = float(arg_id.find_child('weight').children[0].data)
            except AttributeError:
                raise ReaderError('Missing values in arg_id: \'{}\''.format(
                    arg_id))

            # check the weight
            if weight < 0 or weight > 1:
                raise ValueError('weight for {} ({}) is not in range [0,1]'.
                                 format(arg_id, weight))
            else:
                # store the weight in the dictionary for CAES
                self.caes_weight[arg_id] = weight

            # check that the literals are in the PROPOSITION.
            # the checker returns the PropLiteral, so there's no need to
            # convert it again
            ok_c, conclusion = self.check_prop(self.caes_propliteral,
                                               conclusion)
            ok_e, exception = self.check_prop(self.caes_propliteral, exception)
            ok_p, premise = self.check_prop(self.caes_propliteral, premise)

            if ok_c and ok_e and ok_p:
                # store the arguments
                self.caes_argument[arg_id] = \
                    Argument(conclusion = conclusion,
                             premises   = premise,
                             exceptions = exception,
                             weight     = weight,
                             arg_id     = arg_id)

                # add to argset, the state of the argument is treated as None
                # when it is added
                self.argset.add_argument(self.caes_argument[arg_id])

        # -----------------------------------------------------------------
        logging.info('\tAdding parameter to CAES')

        for param in p.parameter.children:
            if param.data == 'alpha':
                self.caes_alpha = float(param.children[0].data)
                # check that they are within range
                if self.caes_alpha > 1 or self.caes_alpha < 0:
                    raise ValueError(
                        'alpha must be within the range of 0 and 1 inclusive. {} given'.
                        format(self.caes_alpha))

            elif param.data == 'beta':
                self.caes_beta = float(param.children[0].data)
                if self.caes_beta > 1 or self.caes_beta < 0:
                    raise ValueError(
                        'beta must be within the range of 0 and 1 inclusive. {} given'.
                        format(self.caes_beta))

            elif param.data == 'gamma':
                self.caes_gamma = float(param.children[0].data)
                if self.caes_gamma > 1 or self.caes_gamma < 0:
                    raise ValueError(
                        'gamma must be within the range of 0 and 1 inclusive. {} given'.
                        format(self.caes_gamma))

        # -----------------------------------------------------------------
        logging.info('\tAdding proofstandard to CAES')
        if len(p.proofstandard.children) == 0:
            # use an empty list hence default PS for all the proposition
            pass
        else:
            for ps in p.proofstandard.children:
                prop_id = ps.data
                prop_ps = ps.children[0].data
                # check validity of prop_id and prop_ps:
                ok, prop_ps = self.check_proofstandard(prop_ps)
                ok, prop_id = self.check_prop(self.caes_propliteral, prop_id)
                # here, create and append the tuple that is used to
                # defined the proofstandard
                self.caes_proofstandard.append((prop_id, prop_ps))

        # -----------------------------------------------------------------
        logging.info('\tAdding issues to CAES')
        for issue in p.issue.children:
            # check that the prop_id are in the set of caes_propliteral
            if self.check_prop(self.caes_propliteral, issue):
                if issue[0] == '-':  # switch the polarity of the propliteral
                    # find the PropLiteral in the dictionary
                    prop = self.caes_propliteral[issue[1:]]
                    prop = prop.negate()
                else:
                    prop = self.caes_propliteral[issue]

            self.caes_issue.add(prop)

        # # -----------------------------------------------------------------
        logging.debug('\talpha:{}, beta:{}, gamme:{}'.format(
            self.caes_alpha, self.caes_beta, self.caes_gamma))
        logging.debug('\tpropliterals: {} '.format(self.caes_propliteral))
        logging.debug('\targuments:{} '.format(
            [arg.__str__() for k, arg in self.caes_argument.items()]))
        logging.debug('\tweights : {}'.format(self.caes_weight))
        logging.debug('\tassumptions: {} '.format(self.caes_assumption))
        logging.debug('\tissues: {} '.format(self.caes_issue))
        logging.debug('\tproofstandard: {}'.format(self.caes_proofstandard))

        # -----------------------------------------------------------------
        # Create file specific directory for graphing
        dot_dir = '../../dot/{}/'.format(path_to_file.split('/')[-1][:-4])
        g_dir = '../../graph/{}/'.format(path_to_file.split('/')[-1][:-4])

        if not os.path.exists(dot_dir):
            os.makedirs(dot_dir)
            os.makedirs(g_dir)
        else:
            # Clearn the folders
            for the_file in os.listdir(dot_dir):
                file_path = os.path.join(dot_dir, the_file)
                if os.path.isfile(file_path) and the_file != 'full.dot':
                    os.unlink(file_path)
            for the_file in os.listdir(g_dir):
                file_path = os.path.join(g_dir, the_file)
                if os.path.isfile(file_path) and the_file != 'full.pdf':
                    os.unlink(file_path)

        if not dialogue:  # dialogue == False
            # define the filename for write_to_graphviz
            dot_filename = dot_dir + 'full.dot'
            g_filename = g_dir + 'full.pdf'
            logging.info('\tInitialising CAES')
            self.run(g_filename, dot_filename)
            return

        elif dialogue:
            logging.debug('Dialogue Mode: On')
            print('dialogue mode on')

            # Go through each issue and generate a dialogue each
            for i, issue in enumerate(self.caes_issue):
                # define the filenames, the number indicates the issue number
                # starting from 1
                dot_filename = dot_dir + '{}_'.format(i + 1)
                g_filename = g_dir + '{}_'.format(i + 1)
                # # self.top_issue = issue
                # dialogue_state_argset, summary, turn_num = \
                #     self.dialogue(issue, g_filename, dot_filename)
                logging.info(
                    '********************************************************************************\nISSUE {}: "{}"\n********************************************************************************'.
                    format(i, issue))

                # Call dialogue class to start the conversation
                d = Dialogue(issue, self.argset, self.caes_assumption,
                             self.caes_weight, self.caes_proofstandard,
                             dot_filename, g_filename, self.run)
                d_argset = d.initialise_dialogue()
                return d_argset

    def run(self,
            g_filename=None,
            dot_filename=None,
            proofstandard=None,
            argset=None,
            issues=None):
        """
        Check if the given argumentation graph is acceptable in the parameters
        parsed - i.e. evaluate in CAES using the proofstandards and the Audience

        :param g_filename : the filename for the pycairo graph
        :param dot_filename : the filename for graphviz dot
        :param argset : for evaluating the issue based on the current
        argumentation graph argset instead of all the arguments parsed.
        :param proofstandard: The proofstandard applicable to the arguments in the argset
        """

        if argset is None:
            argset = self.argset
        if proofstandard is None:
            proofstandard = ProofStandard(self.caes_proofstandard)
        if g_filename is not None and dot_filename is not None:
            argset.draw(g_filename)
            argset.write_to_graphviz(dot_filename)

        # ------------------------------------------------------------
        #       Evaluate the issues using CAES
        # ------------------------------------------------------------
        caes = CAES(
            argset=argset,
            audience=Audience(self.caes_assumption, self.caes_weight),
            proofstandard=proofstandard,
            alpha=self.caes_alpha,
            beta=self.caes_beta,
            gamma=self.caes_gamma)

        if issues is None:
            # Evaluate all the issues that has been parsed
            issues = self.caes_issue
            for issue in issues:
                logging.info('\n\nEvaluating issue: "{}"'.format(issue))
                # use the aceptablility standard in CAES
                acceptability = caes.acceptable(issue)
                logging.info('------ "{}" {} acceptable ------'.format(
                    issue, ['IS NOT', 'IS'][acceptability]))
                print('\n------ "{}" {} acceptable ------'.format(
                    issue, ['IS NOT', 'IS'][acceptability]))

        elif isinstance(issues, PropLiteral):
            # evaluating a single statement usually based on the current
            # argumentation graph
            logging.info('Evaluating issue: "{}"'.format(issues))
            acceptability = caes.acceptable(issues)
            logging.info('------ "{}" {} acceptable ------'.format(
                issues, ['IS NOT', 'IS'][acceptability]))
            print('\n------ "{}" {} acceptable ------'.format(
                issues, ['IS NOT', 'IS'][acceptability]))

            return acceptability

    # ------------------------------------------------------------
    #       Additional Functions to help check
    #       propositions and proofstandards keyed in by the user
    # ------------------------------------------------------------

    def check_prop(self, caes_propliteral, prop_id):
        """
        given the dictionary of caes_propliteral, check if a propliteral with prop_id exists
        If :param: prop_id is a set of strings, iteratively call check_prop on each element in the set.

        :rtype: bool - return True if the prop_id is in caes_propliteral
        :rtype: prop - the PropLiteral of the given prop_id; if a set of prop_id is given, then prop will be a set of PropLiteral
        """

        if type(prop_id) is set:
            props = list(prop_id)
            checker = True
            set_props = set()

            for p in props:
                # recursively calls itself on the all the propliteral in the set
                yes, prop = self.check_prop(caes_propliteral, p)
                checker = checker and yes
                # if no, the function would already had raised an error
                set_props.add(prop)

            return checker, set_props

        elif type(prop_id) is str:
            # check for negation first
            if prop_id[0] == '-':
                prop_id = prop_id[1:]
                negate = 1
            else:
                negate = 0

            # throw error if the key doesnt exists in the dictionary
            if prop_id not in caes_propliteral.keys():
                raise ValueError('"{}" is not defined in PROPOSITION'.format(
                    prop_id))
                return False
            else:
                if negate:
                    return True, caes_propliteral[prop_id].negate()
                else:
                    return True, caes_propliteral[prop_id]

    def check_proofstandard(self, query):
        """
        check if the proofstandard user input is a valid input.
        Return the CAES's version of the similar proofstandard
        """
        standards = {
            'scintilla': "scintilla",
            'preponderance': "preponderance",
            'clear and convincing': "clear_and_convincing",
            'beyond reasonable doubt': "beyond_reasonable_doubt",
            'dialectical validitys': "dialectical_validity"
        }

        if query in standards.keys():
            return True, standards[query]
        else:
            raise ValueError('Invalid proof standard "{}" found'.format(query))


# ========================================================================
#       EXTENSION FOR DIALOGUE
# ========================================================================


class Dialogue(object):
    """
    :class Dialogue simulates the conversation between the proponent and opponent in
    the courthouse
    """

    def __init__(self, issue, caes_argset, caes_assumption, caes_weight,
                 caes_proofstandard, dot_filename, g_filename, run):
        self.top_issue = issue
        self.caes_weight = caes_weight
        self.argset = caes_argset
        self.caes_proofstandard = caes_proofstandard
        self.caes_assumption = caes_assumption

        # variables for the dialogue
        self.dialogue_state_argset = ArgumentSet()
        self.burden_status = None
        self.turn_num = 0
        self.actors = ['PROPONENT', 'RESPONDENT']
        self.summary = ""
        self.dot_filename = dot_filename
        self.g_filename = g_filename
        self.run = run  # function for evaluation
        self.alg_con_argument = 2 # either 1 or 2

    def initialise_dialogue(self):
        # -----------------------------------------------------------------
        # RUN the dialogue
        # -----------------------------------------------------------------
        self.dialogue(self.top_issue)

        # Print the dialogue summary
        logging.info(
            '\n\n\n********************************************************************************DIALOGUE SUMMARY:\n********************************************************************************\n{}********************************************************************************'.
            format(self.summary))
        return self.dialogue_state_argset

    @TraceCalls()
    def dialogue(self, issue):
        """
        ** In dialogue, the proponent and respondent of the issue is not the
        same as the proponent (such as prosecution) and opponent (such as
        defendant) in the setting. A proponent to the issue can be the
        defendant, and the respondent will hence be the prosecutor. This is
        modelled in this function as the turn_num. A odd turn number is the
        proponent of the issue, and the even the respondent.

        :param issue : the issue :type PropLiteral that the propnent and
        opponent are arguing about
        :param g_filename : the filename for the graph to be drawn.
            For each state in a dialogue, a graph will be output.
        :param dot_filename : the filename for the dot file.
            For each state in a dialogue, a dot file will be ouput

        :return summary: the dialogue traces
        :return dialogue_state_argset: the argset of the dialogue
        """
        # -----------------------------------------------------------------
        # Start the dialogue by finding the best pro argument for the issue
        # Note here that the pro argument is not necessarily by the proponent
        # Since it is relative to the issue
        # -----------------------------------------------------------------
        args_pro_issue = self.argset.get_arguments(issue)
        try:
            # Compare the arguments in the full argument set and the current
            # dialogue state. If there are additional arguments, continue the
            # dialogue
            args_pro_issue_dialogue = \
                self.dialogue_state_argset.get_arguments(issue)
            args_pro_issue = [
                arg for arg in args_pro_issue
                if arg not in args_pro_issue_dialogue
            ]
        except KeyError:
            # If there are no arguments leading to the issue in the current
            # argset, continue
            pass

        args_pro_issue = sorted(args_pro_issue, key=lambda args: args.weight)
        try:
            # start with the best argument, i.e. the one with the highest weight
            best_arg_pro = args_pro_issue.pop()
        except IndexError:
            if self.turn_num == 0:
                # If the argument cannot be reached as there is nothing to argue
                # about, then we will just evaluate it according to the full
                # argumentaion set available.
                logging.info(
                    'ISSUE "{}" cannot be evaluated because there are insufficient arguments to form an argumentation graph'.
                    format(issue))
                return False

            else:
                # all arguments pro the issue has been exhausted
                logging.debug(
                    'All pro argument for issue "{}" exhausted'.format(issue))
                # return True so that we know that we should terminate this
                # branch
                return True

        # ------------------------------------------------------------------
        #   Add an argument pro the issue into the argset:
        # ------------------------------------------------------------------
        self.dialogue_state_argset.add_argument(
            best_arg_pro,
            state='claimed',
            claimer=self.actors[self.turn_num % 2])
        self.burden_status = '?'
        # logs the current dialogue state
        self.dialogue_log(issue)

        # ------------------------------------------------------------------
        # check that the proponent of issue have met her burden of proof
        # The evaluation of the Burden of Proof is using scintilla of evidence
        # ------------------------------------------------------------------
        self.burden_met(issue, best_arg_pro)
        self.dialogue_log(issue)

        if not self.burden_status:
            logging.info("{} did not manage to satisfy her burden of proof".
                         format(self.actors[self.turn_num % 2]))
            # Return False as if we cant satisfy this branch, there is no more
            # to argue for!
            return False

        else:
            # ----------------------------------------------------------------
            # At this stage, the burden of proof is satisfied by the proponent
            # of the issue. Hence the respondent takes over
            # The strategy is to find an argument to attack the issue, if we
            # found something that can be acceptable, then we rest, otherwise,
            # Try other pro arguments of the issue
            # ----------------------------------------------------------------
            self.turn_num += 1
            logging.debug('turn_num {}'.format(self.turn_num))

            # The algorithm is set in the class
            if self.alg_con_argument == 1:
                # =========================================================
                # Experiment for finding arguments to defeat the issue:
                # =========================================================
                # Algorithm 1:
                # try to deafeat argument using exceptions first
                # Then find con arguments
                # =========================================================
                logging.debug('USING ALGORITHM 1 TO FIND ARGUMENTS')
                # First we check if the opponent can satisfy the exception:
                try:
                    arg_for_exception = self.find_args_to_exceptions(issue)
                    # since we found an argument to support the issue,
                    # call dialogue on the issue
                    result = self.dialogue(arg_for_exception.conclusion)

                except AttributeError:
                    # occurs when no exceptions found
                    logging.debug(
                        'No arguments found to satisfy exceptions in issue "{}"'.
                        format(issue))

                    # Next, try luck at con arguments!
                    try:
                        # dont use arguments con issue that we are trying to
                        # prove!
                        arg_con_issue = self.find_best_con_argument(issue)
                        result = self.dialogue(arg_con_issue.conclusion)

                    except AttributeError:
                        # occurs when no con argument found
                        self.burden_status = 'NA'
                        return True  # defeated

            elif self.alg_con_argument == 2:
                # =========================================================
                # Algorithm 2:
                # Simultaneously finding argument to prove the exceptions or con
                # arguments to challenge pro arguments
                # This results in the ability to attack the heaviest weighted
                # arguments first
                # =========================================================
                logging.debug('USING ALGORITHM 2 TO FIND ARGUMENTS')
                # =========================================================
                try:
                    arg_found = self.defeat_issue(issue)
                    sub_issue = arg_found.conclusion
                    logging.info('===> sub-issue: {}'.format(sub_issue))
                    result = self.dialogue(sub_issue)

                except AttributeError:
                    # No con arguments to arguments leading to prove the
                    # exceptions found; hence the BOP is NA:
                    self.burden_status = 'NA'
                    return True
            # =========================================================

            # Return to the proponent of the issue:
        logging.info('<=== issue: {}'.format(issue))
        if not result:
            # Burden of proof not met for sub issues:
            if issue == self.top_issue:
                g_file = self.g_filename + 'final.pdf'
                dot_file = self.dot_filename + 'final.dot'
                self.run(g_filename=g_file,
                         dot_filename=dot_file,
                         argset=self.dialogue_state_argset,
                         issues=issue)
                self.dialogue_log(issue)
            return False

        else:
            acceptability = self.run(argset=self.dialogue_state_argset,
                                     issues=issue)
            if acceptability:
                # proponent of issue still wins; we are happy and we shall end!
                logging.info('proponent wins~')
                if issue == self.top_issue:
                    g_file = self.g_filename + 'final.pdf'
                    dot_file = self.dot_filename + 'final.dot'
                    self.run(g_filename=g_file,
                             dot_filename=dot_file,
                             argset=self.dialogue_state_argset,
                             issues=issue)
                    self.dialogue_log(issue)
                return True
            else:
                # If there are still arguments that we can use to tilt the
                # balance (such as in the case of a convergent argument)!
                if len(args_pro_issue):
                    return self.dialogue(issue)
                else:
                    if issue == self.top_issue:
                        g_file = self.g_filename + 'final.pdf'
                        dot_file = self.dot_filename + 'final.dot'
                        self.run(g_filename=g_file,
                                 dot_filename=dot_file,
                                 argset=self.dialogue_state_argset,
                                 issues=issue)
                    return False

    @TraceCalls()
    def burden_met(self, issue, current_argument):
        """
        Checks that the burden of proof of the proponent or opponent is met
        using the CAES acceptability function. The CAES function typically uses
        the 'scintilla of evidence' standard of proof to evaluate the current
        argset. This is because 'scintilla of evidence' ensures that every
        statement is well-supported by having at least one *applicable*
        argument pro the statement. Here, applicable follows CAES definition -
        i.e. the premises of the argument must be acceptable - i.e. in
        caes_assumptions; and none of the exceptions is in the assumptions.

        If the burden of proof is not met for the party, the function
        recurisvely finds evidence to support the premises, such that it is accceptable by CAES.

        When there are NO available arguments in support of the premise, the burden of proof cannot be shifted, and the dialogue will fail.
        """
        # Define evaluation system for checking if burden of proof have been
        # shifted
        caes = CAES(
            argset=self.dialogue_state_argset,
            proofstandard=ProofStandard([]),
            audience=Audience(self.caes_assumption, self.caes_weight))
        logging.info('Checking burden of proof for {}'.format(self.actors[
            self.turn_num % 2]))
        self.burden_status = caes.acceptable(issue)
        logging.info("Burden of Proof: {}".format(self.burden_status))

        if self.burden_status:
            return self.burden_status
        else:
            # if the burden is not met, support the premises to the argument
            for premise in current_argument.premises:
                # find arguments that support the premises
                logging.info('Current Premise: "{}"'.format(premise))
                for arg in self.argset.get_arguments(premise):
                    try:
                        # prevent repeated argument from being added into
                        # argset
                        logging.info('Adding arguments for "{}"'.format(
                            premise))
                        self.dialogue_state_argset.add_argument(
                            arg,
                            state='claimed',
                            claimer=self.actors[self.turn_num % 2])
                        # Needs to manually update the conclusion status
                        # because the node is already in the graph; and adding
                        # its argument will not change the status
                        self.dialogue_state_argset.set_argument_status(
                            arg.conclusion, state='claimed')

                        # Localised checking of the argument:
                        # This is the recurive bit for checking burden of proof
                        self.dialogue_log(issue)
                        self.burden_met(issue, arg)
                        logging.info('')
                        # Check for all the premises:
                        continue

                    except ValueError:
                        logging.info('Nothing to add')
                        return self.burden_status

            return self.burden_status

    @TraceCalls()
    def find_args_to_exceptions(self, issue):
        """
        Given the issue, we consider all the pro arguments and find the hole in
        these arguments where their exceptions can be proved. If there is one,
        return that argument, so that we can create a dialogue for that issue!
        This function does not deals with any burden of proof explicitly. A
        dialogue will be called on the argument's conclusion - i.e. the hole
        that we found. The follow up dialogue then checks the burden of proof is
        satisfiable.
        """
        logging.debug('find_args_to_exceptions in "{}"'.format(issue))
        args_to_consider_ = self.dialogue_state_argset.get_arguments(issue)
        # Consider the args with largest weight first:
        args_to_consider = sorted(
            args_to_consider_, key=lambda arg: arg.weight)

        while len(args_to_consider):
            # iterate through the args
            arg = args_to_consider.pop()
            logging.debug('arg: {}'.format(arg))

            # ----------------------------------------------------------------_
            # first: try to establish the exception:
            exceptions = arg.exceptions

            # get a list of arguments that support the exceptions
            # here, we use the full argset instead of the dialogue argset!
            args_for_exceptions_ = []
            for e in exceptions:
                args_for_exceptions_.extend(self.argset.get_arguments(e))

            # sorted by weight:
            args_for_exceptions = sorted(
                args_for_exceptions_, key=lambda arg: arg.weight)
            logging.debug('exceptions {}'.format(
                [arg.__str__() for arg in args_for_exceptions_]))

            try:
                arg_con = args_for_exceptions.pop()
                # print(arg_con)
                # set the exception to questioned
                self.dialogue_state_argset.set_argument_status(
                    concl=arg_con.conclusion, state='questioned')
                logging.debug('Found an argument to prove the exception')
                return arg_con

            except IndexError:
                # an empty list
                pass

            # ----------------------------------------------------------------_
            # add arguments for sub-issues to the list of arguments to be
            # considered - similar to Breadth First Search
            premises = arg.premises
            for p in premises:
                args_to_consider.extend(
                    self.dialogue_state_argset.get_arguments(p))

            args_to_consider = sorted(
                args_to_consider, key=lambda arg: arg.weight)
            logging.debug('args_to_consider: {}'.format(
                [arg.__str__() for arg in args_to_consider]))
            continue

        # once exhausted all the options, we return
        return False

    @TraceCalls()
    def find_best_con_argument(self, issue):
        """
        Similar to 'find_args_to_exceptions', we consider all arguments pro the
        issue, and find con arguments that can refute it. That is those
        arguments that leads to the negation issue.
        """
        logging.debug('find_best_con_argument for "{}"'.format(issue))
        args_to_consider_ = self.dialogue_state_argset.get_arguments(issue)
        # Consider the args with largest weight first:
        args_to_consider = sorted(
            args_to_consider_, key=lambda arg: arg.weight)

        while len(args_to_consider):
            # iterate through the args
            arg = args_to_consider.pop()
            logging.debug('arg: {}'.format(arg))
            # ----------------------------------------------------------------_
            # find a con argument suing using the full argset
            arg_cons_ = self.argset.get_arguments_con(arg.conclusion)
            arg_cons = sorted(arg_cons_, key=lambda a: a.weight)
            logging.debug('arg_cons {}'.format(
                [arg.__str__() for arg in arg_cons]))

            try:
                arg_con_issue = arg_cons.pop()
                # prevent the same argument that is already in the argset from
                # being added in
                check = self.dialogue_state_argset.get_arguments(
                    arg_con_issue.conclusion)
                if len(check) != 0:
                    logging.debug('argument "{}" has already been added!'.
                                  format(arg_con_issue))
                    continue

                # set the conclusion to questioned!
                self.dialogue_state_argset.set_argument_status(
                    concl=arg.conclusion, state='questioned')
                self.dialogue_state_argset.set_argument_status(
                    concl=arg_con_issue.conclusion, state='claimed')
                logging.debug('Found a con argument')
                return arg_con_issue

            except IndexError:
                pass

            # ----------------------------------------------------------------_
            # add arguments for subissues to the list of arguments to be
            # considered - similar to Breadth First Search
            premises = arg.premises
            for p in premises:
                args_to_consider.extend(
                    self.dialogue_state_argset.get_arguments(p))

            args_to_consider = sorted(
                args_to_consider, key=lambda arg: arg.weight)
            logging.debug('args_to_consider: {}'.format(
                [arg.__str__() for arg in args_to_consider]))
            continue

        return False

    @TraceCalls()
    def defeat_issue(self, issue):
        """
        A cumulative approach for experiment. This is distinct to
        'find_args_to_exceptions' and 'find_best_con_argument' in that it
        searches for an argument that can prove the exception OR a con argument
        simultaneously.

        In other words, this function tries to attack the most heavy weighted
        pro argument first by proving exception or con argument.
        When proving the exception, the argument put forth is the best - in
        terms of weight
        And for con arguments, the function is the heaviest weight as well.
        If two are found, we use the argument with the highest weight
        """
        logging.debug('find arguments to defeat issue "{}"'.format(issue))
        args_to_consider_ = self.dialogue_state_argset.get_arguments(issue)
        # Consider the args with largest weight first:
        args_to_consider = sorted(
            args_to_consider_, key=lambda arg: arg.weight)
        possb_arg = []
        while len(args_to_consider):
            # iterate through the args
            arg = args_to_consider.pop()
            logging.debug('arg: {}'.format(arg))

            # ----------------------------------------------------------------_
            # first: try to establish the exception:
            exceptions = arg.exceptions

            # get a list of arguments that support the exceptions
            # here, we use the full argset instead of the dialogue argset!
            args_for_exceptions_ = []
            for e in exceptions:
                args_for_exceptions_.extend(self.argset.get_arguments(e))

            # sorted by weight:
            args_for_exceptions = sorted(
                args_for_exceptions_, key=lambda arg: arg.weight)
            logging.debug('exceptions {}'.format(
                [arg.__str__() for arg in args_for_exceptions_]))

            try:
                possb_arg1 = args_for_exceptions.pop()
                possb_arg.append((possb_arg1, arg))
            except IndexError:
                # an empty list
                pass

            # ----------------------------------------------------------------_
            # second: find a con argument using using the full argset
            arg_cons_ = self.argset.get_arguments_con(arg.conclusion)
            arg_cons = sorted(arg_cons_, key=lambda a: a.weight)
            logging.debug('arg_cons {}'.format(
                [arg.__str__() for arg in arg_cons]))

            try:
                possb_arg2 = arg_cons.pop()
                # prevent the same argument that is already in the argset from
                # being added in
                check = self.dialogue_state_argset.get_arguments(
                    possb_arg2.conclusion)
                while len(check) != 0:
                    logging.debug('argument "{}" has already been added!'.
                                  format(possb_arg2))
                    possb_arg2 = arg_cons.pop()
                    check = self.dialogue_state_argset.get_arguments(
                        possb_arg2.conclusion)

                possb_arg.append((possb_arg2, arg))
            except IndexError:
                pass

            # ----------------------------------------------------------------_
            # add arguments for subissues to the list of arguments to be
            # considered - similar to Breadth First Search
            premises = arg.premises
            for p in premises:
                args_to_consider.extend(
                    self.dialogue_state_argset.get_arguments(p))

            args_to_consider = sorted(
                args_to_consider, key=lambda arg: arg.weight)
            logging.debug('args_to_consider: {}'.format(
                [arg.__str__() for arg in args_to_consider]))
            continue

        # now, choose the argument with the largest weight
        posb_args = sorted(possb_arg, key=lambda x: x[0].weight)

        try:
            best_con, arg = possb_arg.pop()
        except IndexError:
            logging.info('No arguments found to attack the issue {}'.format(
                issue))
            return False

        if best_con.conclusion == arg.conclusion.negate():
            logging.info('Attacking {} using a con argument: {}'.format(
                arg, best_con))
            self.dialogue_state_argset.set_argument_status(
                concl=best_con.conclusion, state='claimed')
            self.dialogue_state_argset.set_argument_status(
                concl=arg.conclusion, state='questioned')
            return best_con
        else:
            logging.info('Attacking the exception of {} using {}'.format(
                arg, best_con))
            self.dialogue_state_argset.set_argument_status(
                concl=best_con.conclusion, state='questioned')
            return best_con

    def dialogue_log(self, issue, draw=1):
        """
        1) print and log the current dialogue status
            - Which party have the burden of proof
            - the arguments in the current state
            - satisfiability of the burden of proof by the actor
            - the acceptability of the top level issue at the curent level
        2) output the graph for viewing at this turn!
        """
        # --------------------------------------------------------------------
        #   CURRENT STAUS
        # --------------------------------------------------------------------
        logging.info('\n================== turn {} =================='.format(
            self.turn_num))
        self.summary += '================== turn {} =================='.format(
            self.turn_num) + '\n'
        # print Where the BOP lies in for this turn
        logging.info('BURDEN OF PROOF @ {}'.format(self.actors[self.turn_num %
                                                               2]))
        self.summary += 'BURDEN OF PROOF @ {}'.format(self.actors[self.turn_num
                                                                  % 2]) + '\n'
        # --------------------------------------------------------------------
        #   ARGUMENTS
        # --------------------------------------------------------------------
        logging.info('ARGUMENTS:')
        self.summary += 'ARGUMENTS:'
        for arg in self.dialogue_state_argset.arguments:
            logging.info(arg.__str__())
            self.summary += '\n' + arg.__str__()

        # --------------------------------------------------------------------
        #   BURDEN OF PROOF
        # --------------------------------------------------------------------
        logging.info(
            "-----------------------------------------\nBurden of proof met by {} : {}".
            format(self.actors[self.turn_num % 2], self.burden_status))
        self.summary += (
            "\n-----------------------------------------\nBurden of proof met by {} : {}".
            format(self.actors[self.turn_num % 2], self.burden_status))

        # --------------------------------------------------------------------
        # TOP ISSUE:
        # --------------------------------------------------------------------
        logging.info('-----------------------------------------')
        ps = []  # store all the relevant proofstandard
        for arg in self.dialogue_state_argset.arguments:
            # iterate through the arguments, and find the proofstandard used to
            # evaluate the conclusion of these arguments from proofstandards
            # parsed
            concl = arg.conclusion
            ps.extend([(prop_id, prop_ps)
                       for (prop_id, prop_ps) in self.caes_proofstandard
                       if prop_id == concl])

        logging.debug('proofstandard: {}'.format(ps))
        acceptability = self.run(argset=self.dialogue_state_argset,
                                 issues=issue,
                                 proofstandard=ProofStandard(ps))
        self.summary += (
            "\n-----------------------------------------\n\t\tISSUE \"{}\" acceptable? -> {}".
            format(issue, acceptability))

        if self.top_issue != issue:
            acceptability_top = self.run(argset=self.dialogue_state_argset,
                                         issues=self.top_issue,
                                         proofstandard=ProofStandard(ps))
            self.summary += ("\nTOP ISSUE \"{}\" acceptable? -> {}".format(
                self.top_issue, acceptability_top))

        # --------------------------------------------------------------------
        # GRAPHS
        # --------------------------------------------------------------------
        if draw:

            g_file = self.g_filename + str(self.turn_num) + '.pdf'
            dot_file = self.dot_filename + str(self.turn_num) + '.dot'
            num = 1
            if os.path.isfile(g_file):
                g_file = self.g_filename + str(self.turn_num) + '-' + str(
                    num) + '.pdf'
                while os.path.isfile(g_file):
                    num += 1
                    g_file = self.g_filename + str(self.turn_num) + '-' + str(
                        num) + '.pdf'

                dot_file = self.dot_filename + str(self.turn_num) + '-' + str(
                    num) + '.dot'
            self.dialogue_state_argset.draw(g_file)
            self.dialogue_state_argset.write_to_graphviz(dot_file)
        logging.info('============================================\n')
        self.summary += '\n============================================\n'


# ========================================================================
#       CAES
# ========================================================================


class PropLiteral(object):
    """
    Proposition literals have most of the properties of ordinary strings,
    except that the negation method is Boolean; i.e.

    >>> a = PropLiteral('a')
    >>> a.negate().negate() == a
    True
    """

    def __init__(self, string, polarity=True):
        """
        Propositions are either positive or negative atoms.
        """
        self.polarity = polarity
        # self._string = "\\n".join(wrap(repr(string), 30))
        self._string = string

    def negate(self):
        """
        Negation of a proposition.

        We create a copy of the current proposition and flip its polarity.
        """
        polarity = (not self.polarity)
        return PropLiteral(self._string, polarity=polarity)

    def __str__(self):
        """
        Override ``__str__()`` so that negation is realised as a prefix on the
        string.
        """
        if self.polarity:
            return self._string
        return "-" + self._string

    def __hash__(self):
        return self._string.__hash__()

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__str__() == other.__str__()
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.__str__() < other.__str__()


# ========================================================================


class Argument(object):
    """
    An argument consists of a conclusion, a set of premises and a set of
    exceptions (both of which can be empty).

    Although arguments should have identifiers (`arg_id`), it is preferable
    to specify these when calling the :meth:`add_argument` method of
    :class:`ArgumentSet`.
    """

    def __init__(self,
                 conclusion,
                 premises=set(),
                 exceptions=set(),
                 weight=0,
                 arg_id=None):
        """
        :param conclusion: The conclusion of the argument.
        :type conclusion: :class:`PropLiteral`
        :param premises: The premises of the argument.
        :type premises: set(:class:`PropLiteral`)
        :param exceptions: The exceptions of the argument
        :type exceptions: set(:class:`PropLiteral`)
        """

        self.conclusion = conclusion
        self.premises = premises
        self.exceptions = exceptions
        self.weight = weight
        self.arg_id = arg_id

    def __str__(self):
        """
        Define print string for arguments.

        We follow similar conventions to those used by the CarneadesDSL
        Haskell implementation.

        Premises and exceptions are sorted to facilitate doctest comparison.
        """
        if len(self.premises) == 0:
            prems = "[]"
        else:
            prems = sorted(self.premises)

        if len(self.exceptions) == 0:
            excepts = "[]"
        else:
            excepts = sorted(self.exceptions)
        return "{}, ~{} => {}".format(prems, excepts, self.conclusion)


# ========================================================================


class ArgumentSet(object):
    """
    An ``ArgumentSet`` is modeled as a dependency graph where vertices represent
    the components of an argument. A vertex corresponding to the conclusion
    of an argument *A* will **depend on** the premises and exceptions in *A*.

    The graph is built using the `igraph <http://igraph.org/>`_ library. This
    allows *attributes* to be associated with both vertices and edges.
    Attributes are represented as Python dictionaries where the key (which
    must be a string) is the name of the attribute and the value is the
    attribute itself. For more details, see the
    `igraph tutorial\
    <http://igraph.org/python/doc/tutorial/tutorial.html#setting-and-retrieving-attributes>`_.
    """

    def __init__(self):
        self.graph = Graph()
        self.graph.to_directed()  # set up as a directed graph
        self.arg_count = 0
        self.arguments = []

    def propset(self):
        """
        The set of :class:`PropLiteral`s represented by the vertices in
        the graph.

        Retrieving this set relies on the fact that :meth:`add_proposition`
        sets a value for the ``prop`` attribute in vertices created when a
        new proposition is added to the graph.
        """
        g = self.graph
        props = set()
        try:
            props = {p for p in g.vs['prop']}
        except KeyError:
            pass
        return props

    def add_proposition(self, proposition, state=None):
        """
        Add a proposition to a graph if it is not already present as a vertex.

        :param proposition: The proposition to be added to the graph.
        :type proposition: :class:`PropLiteral`
        :return: The graph vertex corresponding to the proposition.
        :rtype: :class:`Graph.Vertex`
        :raises TypeError: if the input is not a :class:`PropLiteral`.
        """
        if isinstance(proposition, PropLiteral):
            if proposition in self.propset():
                logging.debug("Proposition '{}' is already in graph".format(
                    proposition))

            else:
                # add the proposition as a vertex attribute, recovered via the
                # key 'prop'
                self.graph.add_vertex(prop=proposition, state=state)
                logging.debug("Added proposition '{}' to graph with state {}".
                              format(proposition, state))
            # return the vertex
            return self.graph.vs.select(prop=proposition)[0]

        else:
            raise TypeError('Input {} should be PropLiteral'.format(
                proposition))

    def add_argument(self, argument, state=None, claimer=None):
        """
        Add an argument to the graph.
        All vertex in the graph have either the 'arg' or 'prop' attribute

        For 'arg' vertex - the arguments, the default state is None.
        To illustrate the shifting burden of proof, the state will be updated
        as a member of {claimed, questioned}

        For edges between the 'arg' and 'prop' vertex, the `is_exception` field
        denotes whether the premise is an exception.  This is required as the
        respondent have the Burden of Proof for the exceptions to defeat the
        argument.

        :parameter argument: The argument to be added to the graph.
        :type argument: :class:`Argument`
        :parameter arg_id: The ID of the argument
        :type arg_id: str or None
        """
        g = self.graph
        if argument in self.arguments:
            raise ValueError('"{}" is already in the argument set'.format(
                argument))
        self.arguments.append(argument)  # store a list of arguments
        self.arg_count += 1  # keep track of the number of arguments
        # -----------------------------------------------------------
        #   VERTICES
        # -----------------------------------------------------------
        # add the arg_id as a vertex attribute, recovered via the 'arg' key
        self.graph.add_vertex(arg=argument.arg_id, claimer=claimer)
        logging.info('Added argument \'{}\' to graph by \'{}\''.format(
            argument.arg_id, claimer))
        # returns the vertex that goes to the argument
        arg_v = g.vs.select(arg=argument.arg_id)[0]
        # add proposition vertices to the graph
        # conclusion:
        if state is not None:
            assert state == 'claimed' or state == 'questioned'
        conclusion_v = self.add_proposition(argument.conclusion, state=state)
        # automatically add the negated state for conclusion
        self.add_proposition(argument.conclusion.negate())
        # premise:
        premise_vs = [
            self.add_proposition(prop) for prop in sorted(argument.premises)
        ]
        # exception:
        exception_vs = [
            self.add_proposition(prop) for prop in sorted(argument.exceptions)
        ]
        # -----------------------------------------------------------
        #   EDGES
        # -----------------------------------------------------------
        # add new edges to the graph
        # add edge from conclusion to argument
        g.add_edge(conclusion_v.index, arg_v.index, is_exception=False)
        # add edges from argument to the premise and exceptions
        for target in premise_vs:
            g.add_edge(arg_v.index, target.index, is_exception=False)
        for target in exception_vs:
            g.add_edge(arg_v.index, target.index, is_exception=True)
        return

    def get_arguments(self, proposition):
        """
        Find the arguments for a proposition in an *ArgumentSet*.

        :param proposition: The proposition to be checked.
        :type proposition: :class:`PropLiteral`
        :return: A list of the arguments pro the proposition
        :rtype: list(:class:`Argument`)

        :raises ValueError: if the input :class:`PropLiteral` isn't present\
        in the graph.
        """
        g = self.graph

        # index of vertex associated with the proposition
        vs = g.vs.select(prop=proposition)

        try:
            conc_v_index = vs[0].index
            # IDs of vertices reachable in one hop from the proposition's
            # vertex (i.e. the argument vertices)
            target_IDs = [e.target for e in g.es.select(_source=conc_v_index)]
            # the vertices indexed by target_IDs
            out_vs = [g.vs[i] for i in target_IDs]

            # a list of argument id that is connected to the conclusion
            arg_IDs = [v['arg'] for v in out_vs]
            # return the arguments
            args = [arg for arg in self.arguments if arg.arg_id in arg_IDs]
            return args

        except IndexError:
            raise ValueError("Proposition '{}' is not in the current graph".
                             format(proposition))

    def get_arguments_con(self, proposition):
        """
        Given a proposition p, use get_arguments to find the arguments that are are con p

        :param proposition: The proposition to checked.
        :type proposition: :class:`PropLiteral`
        """
        return self.get_arguments(proposition.negate())

    def get_arguments_status(self, status):
        """
        Find the argument(s) whose conclusion is of `questioned` or `claimed`
        which leads to the issue

        :param status - a member {claimed, questioned}
        :raise ValueError if the status is not of claimed or questioned
        """
        if str(status) != 'claimed' and str(status) != 'questioned':
            raise ValueError('{} is not a valid status'.format(status))
        else:
            vs = self.graph.vs.select(state=status)
            try:
                conc_v_index = vs[0].index
            except IndexError:
                return []

            args = []
            for i in vs.indices:
                # iterate through the conclusion vertices and call
                # get_arguments to find the Arguments
                concl = self.graph.vs[i]['prop']
                args_concl = self.get_arguments(concl)
                args.extend(args_concl)

        logging.debug('found args with status "{}": {}'.format(
            status, [str(arg) for arg in args]))
        return args

    def get_arguments_claimer(self, claimer):
        """
        Get arguments made by the claimer - either 'PROPONENT' or 'RESPONDENT'
        """
        if str(claimer) != 'PROPONENT' and str(claimer) != 'RESPONDENT':
            raise ValueError('{} is not a valid claimer'.format(claimer))
        else:
            # this is an verticeset of argument ID
            vs = self.graph.vs.select(claimer=claimer)
            args = []
            for v in vs.indices:
                arg_id = self.graph.vs[v]['arg']
                args.extend(
                    [arg for arg in self.arguments if arg.arg_id == arg_id])
            return args

    def set_argument_status(self, concl, state):
        """
        Update the status of the argument's conclusion to either
        {claimed, questioned}
        """
        self.graph.vs.select(prop=concl)['state'] = state
        logging.info('proposition "{}" state updated to "{}"'.format(concl,
                                                                     state))
        # # DEBUG
        # for i in self.graph.vs.indices:
        #     print(self.graph.vs[i])

    def draw(self, g_filename, debug=False):
        """
        Visualise an :class:`ArgumentSet` as a labeled graph.
        This uses the pycairo and python-igraph module.

        :parameter debug: If :class:`True`, add the vertex index to the label.
        """
        g = self.graph

        # labels for nodes that are classed as propositions
        labels = g.vs['prop']

        # insert the labels for nodes that are classed as arguments
        for i in range(len(labels)):
            if g.vs['arg'][i] is not None:
                labels[i] = g.vs['arg'][i]

        if debug:
            d_labels = []
            for (i, label) in enumerate(labels):
                d_labels.append("{}\nv{}".format(label, g.vs[i].index))
            labels = d_labels

        g.vs['label'] = labels

        roots = [i for i in range(len(g.vs)) if g.indegree()[i] == 0]
        ALL = 3  # from igraph
        layout = g.layout_reingold_tilford(mode=ALL, root=roots)

        plot_style = {}
        # for vertexes
        # arguments : pink and rectangular
        # propositions : blue and circle
        plot_style['vertex_color'] = []
        # plot_style['vertex_color'] = \
        #     ['lightblue' if x is None else 'pink' for x in g.vs['arg']]
        counter = 0
        for i, x in enumerate(g.vs['arg']):
            if x is None:  # if it is an arguments
                # By argument status = 'claimed' or 'questioned':
                status = g.vs[i]['state']
                if status == 'claimed':
                    plot_style['vertex_color'].append('lightblue')
                elif status == 'questioned':
                    plot_style['vertex_color'].append('purple')
                else:
                    plot_style['vertex_color'].append('gray')
            else:
                # darker red = larger weight
                how_red = [1, 1 - self.arguments[counter].weight, 0.5]
                # By argument status = 'claimed' or 'questioned':
                plot_style['vertex_color'].append(how_red)
                by = g.vs[i]['claimer']
                counter += 1

        plot_style['vertex_shape'] = \
            ['circular' if g.vs[x]['arg'] is None else 'diamond' if g.vs[x]['claimer'] == 'PROPONENT' else 'rect' for x in g.vs.indices]
        plot_style['vertex_size'] = 25
        # use thicker lines if the node is an exception of the argument
        plot_style["edge_width"] = [
            1 + 2 * int(is_exception) for is_exception in g.es["is_exception"]
        ]
        # rotation, 0 is right of the vertex
        plot_style['vertex_label_angle'] = 1.5
        plot_style['vertex_label_dist'] = -2
        # plot_style['vertex_label_size'] = 20
        # General plot
        plot_style['margin'] = (100, 100, 100, 100)  # pixels of border
        plot_style['bbox'] = (1000, 600)  # change the size of the image
        plot_style['layout'] = layout
        # execute the plot
        plot(g, g_filename, autocurve=True, **plot_style)
        return

    def write_to_graphviz(self, fname=None):
        g = self.graph
        result = "digraph G{ \n"
        counter = 0

        for vertex in g.vs:
            arg_label = vertex.attributes()['arg']
            prop_label = vertex.attributes()['prop']

            # If the vertex is an argument
            if arg_label:
                arg_weight = self.arguments[counter].weight
                # higher weights = darker color
                if arg_weight <= 0.2:
                    color = 'coral'
                elif arg_weight <= 0.4 and arg_weight > 0.2:
                    color = 'coral1'
                elif arg_weight <= 0.6 and arg_weight > 0.4:
                    color = 'coral2'
                elif arg_weight <= 0.8 and arg_weight > 0.6:
                    color = 'coral3'
                else:
                    color = 'coral4'
                arg_label = "\\n".join(
                    wrap(repr(arg_label), 40))  # wrap at length
                dot_str = ('"{}"'.format(arg_label) +
                           ' [color="black", fillcolor="{}",'.format(color) +
                           'fixedsize=false, shape=box, style="filled"]; \n')
                counter += 1

            # if the vertex is a proposition
            elif prop_label:
                prop_label = "\\n".join(wrap(repr(prop_label), 40))
                dot_str = ('"{}"'.format(prop_label) +
                           ' [color="black", fillcolor="lightblue", '
                           'fixedsize=false,  shape="box", '
                           'style="rounded,filled"]; \n')
            result += dot_str

        for edge in g.es:
            source_label = g.vs[edge.source]['prop'] if\
                g.vs[edge.source]['prop'] else g.vs[edge.source]['arg']
            target_label = g.vs[edge.target]['prop'] if\
                g.vs[edge.target]['prop'] else g.vs[edge.target]['arg']
            source_label = "\\n".join(wrap(repr(source_label), 40))
            target_label = "\\n".join(wrap(repr(target_label), 40))
            # if edge is an exception, use a dot instead of arrow
            if edge.attributes()['is_exception']:
                result += '"{}" -> "{}" [arrowhead=dot]'.format(source_label,
                                                                target_label)
            else:
                result += '"{}" -> "{}"'.format(source_label, target_label)
            dot_str = " ; \n"
            result += dot_str

        result += "}"

        # Write to file
        if fname is None:
            fname = 'graph.dot'

        with open(fname, 'w') as f:
            print(result, file=f)
        return


# ========================================================================


class ProofStandard(object):
    """
    Each proposition in a CAES is associated with a proof standard.

    A proof standard is initialised by supplying a (possibly empty) list of
    pairs, each consisting of a proposition and the name of a proof standard.

    >>> intent = PropLiteral('intent')
    >>> ps = ProofStandard([(intent, "beyond_reasonable_doubt")])

    Possible values for proof standards: `"scintilla"`, `"preponderance"`,
    `"clear_and_convincing"`, `"beyond_reasonable_doubt"`, and
    `"dialectical_validity"`.
    """

    def __init__(self, propstandards, default='scintilla'):
        """
        :param propstandards: the proof standard associated with\
        each proposition under consideration.
        :type propstandards: list(tuple(:class:`PropLiteral`, str))
        """
        self.proof_standards = [
            "scintilla", "preponderance", "clear_and_convincing",
            "beyond_reasonable_doubt", "dialectical_validity"
        ]
        self.default = default
        self.config = defaultdict(lambda: self.default)
        self._set_standard(propstandards)

    def _set_standard(self, propstandards):
        for (prop, standard) in propstandards:
            if standard not in self.proof_standards:
                raise ValueError("{} is not a valid proof standard".format(
                    standard))
            self.config[prop] = standard

    def get_proofstandard(self, proposition):
        """
        Determine the proof standard associated with a proposition.

        :param proposition: The proposition to be checked.
        :type proposition: :class:`PropLiteral`
        """
        return self.config[proposition]

    def __str__(self):
        return print(self.config)

    def __repr__(self):
        return self.__str__()


# ========================================================================

Audience = namedtuple('Audience', ['assumptions', 'weight'])
"""
An audience has assumptions about which premises hold and also
assigns weights to arguments.

:param assumptions: The assumptions held by the audience
:type assumptions: set(:class:`PropLiteral`)

:param weights: An mapping from :class:`Argument`\ s to weights.
:type weights: dict
"""

# ========================================================================


class CAES(object):
    """
    A class that represents a Carneades Argument Evaluation Structure (CAES).

    """

    def __init__(self,
                 argset,
                 audience,
                 proofstandard,
                 alpha=0.4,
                 beta=0.3,
                 gamma=0.2):
        """
        :parameter argset: the argument set used in the CAES
        :type argset: :class:`ArgSet`

        :parameter audience: the audience for the CAES
        :type audience: :class:`Audience`

        :parameter proofstandard: the proof standards used in the CAES
        :type proofstandard: :class:`ProofStandard`

        :parameter alpha: threshold of strength of argument required for a\
        proposition to reach the proof standards "clear and convincing" and\
        "beyond reasonable doubt".

        :type alpha: float in interval [0, 1]


        :parameter beta: difference required between strength of\
        argument *pro* a proposition vs strength of argument *con*\
        to reach the proof standard "clear and convincing".

        :type beta: float in interval [0, 1]

        :parameter gamma: threshold of strength of a *con* argument required\
        for a proposition to reach the proof standard "beyond reasonable\
        doubt".

        :type gamma: float in interval [0, 1]
        """
        self.argset = argset
        self.assumptions = audience.assumptions
        self.weight = audience.weight
        self.standard = proofstandard
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def get_all_arguments(self):
        """
        Show all arguments in the :class:`ArgSet` of the CAES.
        """
        for arg in self.argset.arguments:
            print(arg)

    @TraceCalls()
    def applicable(self, argument):
        """
        An argument is *applicable* in a CAES if it needs to be taken into
        account when evaluating the CAES.

        :parameter argument: The argument whose applicablility is being\
        determined.

        :type argument: :class:`Argument`
        :rtype: bool
        """
        _acceptable = lambda p: self.acceptable(p)
        return self._applicable(argument, _acceptable)

    def _applicable(self, argument, _acceptable):
        """
        :parameter argument: The argument whose applicablility is being
        determined.

        :type argument: :class:`Argument`

        :parameter _acceptable: The function which determines the
        acceptability of a proposition in the CAES.

        :type _acceptable: LambdaType
        :rtype: bool
        """
        logging.debug('Checking applicability of {}...'.format(
            argument.arg_id))
        logging.debug('Current assumptions: {}'.format(self.assumptions))
        logging.debug('Current premises: {}'.format(argument.premises))

        # Checking the applicablility of the premises
        #
        b1 = all(
            p in self.assumptions or
            (p.negate() not in self.assumptions and _acceptable(p))
            for p in argument.premises)

        #  Checking applicablility of exceptions
        if argument.exceptions:
            logging.debug('Current exception: {}'.format(argument.exceptions))
        b2 = all(
            e not in self.assumptions and (e.negate() in self.assumptions or
                                           not _acceptable(e))
            for e in argument.exceptions)

        return b1 and b2

    @TraceCalls()
    def acceptable(self, proposition):
        """
        A conclusion is *acceptable* in a CAES if it can be arrived at under
        the relevant proof standards, given the beliefs of the audience.

        :param proposition: The conclusion whose acceptability is to be\
        determined.

        :type proposition: :class:`PropLiteral`

        :rtype: bool
        """

        standard = self.standard.get_proofstandard(proposition)
        logging.debug("Checking whether proposition '{}' "
                      "meets proof standard '{}'.".format(proposition,
                                                          standard))
        return self.meets_proof_standard(proposition, standard)

    @TraceCalls()
    def meets_proof_standard(self, proposition, standard):
        """
        Determine whether a proposition meets a given proof standard.

        :param proposition: The proposition which should meet the relevant\
        proof standard.

        :type proposition: :class:`PropLiteral`

        :parameter standard: a specific level of proof;\
        see :class:`ProofStandard` for admissible values

        :type standard: str
        :rtype: bool

        """
        arguments = self.argset.get_arguments(proposition)
        logging.debug('\targuments:{} '.format(
            [arg.__str__() for arg in arguments]))

        result = False

        if standard == 'scintilla':
            # at least one applicable argument pro p
            result = any(arg for arg in arguments if self.applicable(arg))
        elif standard == 'preponderance':
            # maximum weight of the applicable arguments pro p is grater than
            # the maximum weight of the applicable arguments con p
            result = self.max_weight_pro(proposition) > \
                self.max_weight_con(proposition)
        elif standard == 'clear_and_convincing':
            # weight difference between the max weight pro and max weight con
            # should be larger than beta
            # and applicable argument pro p should be stronger than a given
            # constant alpha
            mwp = self.max_weight_pro(proposition)
            mwc = self.max_weight_con(proposition)
            exceeds_alpha = mwp > self.alpha
            diff_exceeds_gamma = (mwp - mwc) > self.gamma
            logging.debug("max weight pro '{}' is {}".format(proposition, mwp))
            logging.debug("max weight con '{}' is {}".format(proposition, mwc))
            logging.debug("max weight pro '{}' >  alpha '{}': {}".format(
                mwp, self.alpha, exceeds_alpha))
            logging.debug("diff between pro and con = {} > gamma: {}".format(
                mwp - mwc, diff_exceeds_gamma))

            result = (mwp > self.alpha) and (mwp - mwc > self.gamma)
        elif standard == 'beyond_reasonable_doubt':
            # strongest argument con p needs to be less than a given constant
            # gamma AND ssatisfy clean and convincing (defined above)
            result = \
                self.meets_proof_standard(proposition,
                                          'clear_and_convincing') \
                and \
                self.max_weight_con(proposition) < self.gamma

        return result

    def weight_of(self, argument):
        """
        Retrieve the weight associated by the CAES audience with an argument.

        :parameter argument: The argument whose weight is being determined.
        :type argument: :class:`Argument`
        :return: The weight of the argument.
        :rtype: float in interval [0, 1]
        """
        arg_id = argument.arg_id
        try:
            return self.weight[arg_id]
        except KeyError:
            raise ValueError("No weight assigned to argument '{}'.".format(
                arg_id))

    def max_weight_applicable(self, arguments):
        """
        Retrieve the weight of the strongest applicable argument in a list
        of arguments.

        :parameter arguments: The arguments whose weight is being compared.
        :type arguments: list(:class:`Argument`)
        :return: The maximum of the weights of the arguments.
        :rtype: float in interval [0, 1]
        """
        arg_ids = [arg.arg_id for arg in arguments]

        applicable_args = [arg for arg in arguments if self.applicable(arg)]
        if len(applicable_args) == 0:
            logging.debug('No applicable arguments in {}'.format(arg_ids))
            return 0.0

        applic_arg_ids = [arg.arg_id for arg in applicable_args]
        logging.debug('Checking applicability and weights of {}'.format(
            applic_arg_ids))
        weights = [self.weight_of(argument) for argument in applicable_args]
        logging.debug('Weights of {} are {}'.format(applic_arg_ids, weights))
        return max(weights)

    def max_weight_pro(self, proposition):
        """
        The maximum of the weights pro the proposition.

        :param proposition: The conclusion whose acceptability is to be\
        determined.

        :type proposition: :class:`PropLiteral`
        :rtype: float in interval [0, 1]
        """
        args = self.argset.get_arguments(proposition)
        return self.max_weight_applicable(args)

    def max_weight_con(self, proposition):
        """
        The maximum of the weights con the proposition.

        :param proposition: The conclusion whose acceptability is to be\
        determined.

        :type proposition: :class:`PropLiteral`
        :rtype: float in interval [0, 1]
        """
        con = proposition.negate()
        args = self.argset.get_arguments(con)
        return self.max_weight_applicable(args)


# -----------------------------------------------------------------------------
#       MAIN
# -----------------------------------------------------------------------------
# Set the DOCTEST to True, if want to run doctests
DOCTEST = False

if __name__ == '__main__':

    if DOCTEST:
        import doctest
        doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE)
    else:
        import argparse
        argparser = argparse.ArgumentParser(
            description="Welcome to Carneades Argument Evaluation System.\n")
        argparser.add_argument(
            'pathname',
            nargs='+',
            default='"../../samples/example.yml"',
            help='path to each of your .yml file(s). At least one must be given (example: %(default)s)'
        )
        argparser.add_argument(
            '-d',
            '--dialogue',
            dest='dialogue',
            help='shows the shifting burden of proof while the arguments are evaluated in CAES. If the flag is used, dialogue mode will be used for all the files',
            action='store_true')
        argparser.add_argument(
            '-logger',
            dest='logger',
            help='logging level (default: %(default)s)',
            choices=['DEBUG', 'INFO'],
            default='DEBUG',
            type=str,
            action='store')
        argparser.add_argument(
            '-buffer',
            '--buffer_size',
            dest='buffer_size',
            help='set the buffer size of the reader (default: %(default)s)',
            required=False,
            action='store',
            default=4096,
            type=int)
        argparser.add_argument(
            '-indent',
            '--indent_size',
            dest='indent_size',
            help='set the indent_size used in the .yml files (default: %(default)s)',
            action='store',
            default=2,
            type=int)

        args = vars(argparser.parse_args())
        # print(args)
        # print('indent size = {}'.format(args.indent_size))
        # print('buffer size = {}'.format(args.buffer_size))
        filenames = args['pathname']

        # Some argument is passed:
        file_check = filenames[0]

        if os.path.isdir(str(file_check)):
            print(
                'You have given a directory!\nUsage: $ python caes.py path_to_file | [path_to_file]+'
            )
            exit()

        elif len(filenames) > 1:  # if user gave a list of filenames
            # inform the number of files
            print('{} files detected'.format(len(filenames)))

            for filename in filenames:
                logger_file = '../../log/{}.log'.format(
                    filename.split('/')[-1][:-4])
                logging.basicConfig(
                    format='%(message)s',
                    level=args['logger'],
                    filemode='w',
                    filename=logger_file)

                # check that the filename parsed are all files
                assert os.path.isfile(filename), logging.exception(
                    '{} is not a file'.format(filename))
                print('\nProcessing {}'.format(filename))

                Reader(
                    buffer_size=args['buffer_size'],
                    indent_size=args['indent_size']).load(
                        filename, dialogue=args['dialogue'])

                logger = logging.getLogger()
                logger.removeHandler(logger.handlers[0])

        else:
            if os.path.isfile(file_check):
                logger_file = '../../log/{}.log'.format(
                    file_check.split('/')[-1][:-4])
                logging.basicConfig(
                    format='%(message)s',
                    level=args['logger'],
                    filemode='w',
                    filename=logger_file)

                # check that the filename parsed are all files
                assert os.path.isfile(file_check), logging.exception(
                    '{} is not a file'.format(filename))
                print('\nProcessing {}'.format(file_check))

                Reader(
                    buffer_size=args['buffer_size'],
                    indent_size=args['indent_size']).load(
                        file_check, dialogue=args['dialogue'])

            else:
                logging.error('Cannot find file {}'.format(filenames))
                exit()
