# Carneades Argument Evaluation Structure
#
# Copyright (C) 2014 Ewan Klein
# Author: Ewan Klein <ewan@inf.ed.ac.uk>
# Based on: https://hackage.haskell.org/package/CarneadesDSL
#
# For license information, see LICENSE

"""
==========
 Overview
==========

Propositions
============

First, let's create some propositions using the :class:`PropLiteral`
constructor. All propositions are atomic, that is, either positive or
negative literals.

>>> kill = PropLiteral('kill')
>>> kill.polarity
True
>>> intent = PropLiteral('intent')
>>> murder = PropLiteral('murder')
>>> witness1 = PropLiteral('witness1')
>>> unreliable1 = PropLiteral('unreliable1')
>>> witness2 = PropLiteral('witness2')
>>> unreliable2 = PropLiteral('unreliable2')

The :meth:`negate` method allows us to introduce negated propositions.

>>> neg_intent = intent.negate()
>>> print(neg_intent)
-intent
>>> neg_intent.polarity
False
>>> neg_intent == intent
False
>>> neg_intent.negate() == intent
True

Arguments
=========

Arguments are built with the :class:`Argument` constructor. They are required
to have a conclusion, and may aiulso have premises and exceptions.

>>> arg1 = Argument(murder, premises={kill, intent})
>>> arg2 = Argument(intent, premises={witness1}, exceptions={unreliable1})
>>> arg3 = Argument(neg_intent, premises={witness2}, exceptions={unreliable2})
>>> print(arg1)
[intent, kill], ~[] => murder

In order to organise the dependencies between the conclusion of an argument
and its premises and exceptions, we model them using a directed graph called
an :class:`ArgumentSet`. Notice that the premise of one argument (e.g., the
``intent`` premise of ``arg1``) can be the conclusion of another argument (i.e.,
``arg2``)).

>>> argset = ArgumentSet()
>>> argset.add_argument(arg1, arg_id='arg1')
>>> argset.add_argument(arg2, arg_id='arg2')
>>> argset.add_argument(arg3, arg_id='arg3')

There is a :func:`draw` method which allows us to view the resulting graph.

>>> argset.draw() # doctest: +SKIP

Proof Standards
===============

In evaluating the relative value of arguments for a particular conclusion
``p``, we need to determine what standard of *proof* is required to establish
``p``. The notion of proof used here is not formal proof in a logical
system. Instead, it tries to capture how substantial the arguments are
in favour of, or against, a particular conclusion.

The :class:`ProofStandard` constructor is initialised with a list of
``(proposition, name-of-proof-standard)`` pairs. The default proof standard,
viz., ``'scintilla'``, is the weakest level.  Different
propositions can be assigned different proof standards that they need
to attain.

>>> ps = ProofStandard([(intent, "beyond_reasonable_doubt")],
... default='scintilla')

Carneades Argument Evaluation Structure
=======================================

The core of the argumentation model is a data structure plus set of
rules for evaluating arguments; this is called a Carneades Argument
Evaluation Structure (CAES). A CAES consists of a set of arguments,
an audience (or jury), and a method for determining whether propositions
satisfy the relevant proof standards.

The role of the audience is modeled as an :class:`Audience`, consisting
of a set of assumed propositions, and an assignment of weights to
arguments.

>>> assumptions = {kill, witness1, witness2, unreliable2}
>>> weights = {'arg1': 0.8, 'arg2': 0.3, 'arg3': 0.8}
>>> audience = Audience(assumptions, weights)

Once an audience has been defined, we can use it to initialise a
:class:`CAES`, together with instances of :class:`ArgumentSet` and
:class:`ProofStandard`:

>>> caes = CAES(argset, audience, ps)
>>> caes.get_all_arguments()
[intent, kill], ~[] => murder
[witness1], ~[unreliable1] => intent
[witness2], ~[unreliable2] => -intent

The :meth:`get_arguments` method returns the list of arguments in an
:class:`ArgumentSet` which support a given proposition.

A proposition is said to be *acceptable* in a CAES if it meets its required
proof standard. The process of checking whether a proposition meets its proof
standard requires another notion: namely, whether the arguments that support
it are *applicable*. An argument ``arg`` is applicable if and only if all its
premises either belong to the audience's assumptions or are acceptable;
moreover, the exceptions of ``arg`` must not belong to the assumptions or be
acceptable. For example, `arg2`, which supports the conclusion `intent`, is
acceptable since `witness1` is an assumption, while the exception
`unreliable1` is neither an assumption nor acceptable.

>>> arg_for_intent = argset.get_arguments(intent)[0]
>>> print(arg_for_intent)
[witness1], ~[unreliable1] => intent
>>> caes.applicable(arg_for_intent)
True

>>> caes.acceptable(intent)
False

Although there is an argument (``arg3``) for `-intent`, it is not applicable,
since the exception `unreliable2` does belong to the audience's assumptions.

>>> any(caes.applicable(arg) for arg in argset.get_arguments(neg_intent))
False

This in turn has the consequence that `-intent` is not acceptable.

>>> caes.acceptable(neg_intent)
False

Despite the fact that the argument `arg2` for `murder` is applicable,
the conclusion `murder` is not acceptable, since

>>> caes.acceptable(murder)
False
>>> caes.acceptable(murder.negate())
False
"""


from collections import namedtuple, defaultdict
import logging
import os
import sys
from textwrap import wrap
from igraph import Graph, plot

# fix to ensure that package is loaded properly on system path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from carneades.tracecalls import TraceCalls
from carneades.tokenizer import Tokenizer
from carneades.parser import Parser, Node
from carneades.error import ReaderError

# ========================================================================
#           READER
# ========================================================================


class Reader(object):
    """
    Reader class encapsulates the processing of the file using the load function
    ---
    DOCTEST:
    >>> reader = Reader(); # use default buffer_size
    >>> reader.load('../../samples/example.yml', dialogue=False)
    <BLANKLINE>
    ------ accused committed murder IS NOT acceptable ------
    <BLANKLINE>
    ------ -accused committed murder IS NOT acceptable ------

    """

    def __init__(self, buffer_size=4096, indent_size=2):
        """
        Initialise the Reader to read your source file with the user's settings
        ----
        PARAMETER:
        :param buffer_size: defaults to 4096
        :param indent_size: defaults to 2
        """
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
        self.actors = ['PROPONENT', 'OPPONENT']

    def load(self, path_to_file, dialogue):
        """
        load the file of interest, tokenize and parse it. Using the information given by the user in the file(s), call CAES to evaluate the arguments
        -----
        :param path_to_file : the path to the file to be opened
        :param dialogue : If `dialogue = False`, the acceptability check be shown. Otherwise, if `dialogue = True`, a dialogue version of the arguments will be shown. The class:dialogue illustrates the shifting BOP between the
        proponent and opponent at each class:stage. At each stage, the best argument is put forth so as to attack the claim by the based on the party with the burden of proof.
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

        # ---------------------------------------------------------------
        #   Parsing:
        # ---------------------------------------------------------------
        logging.info('\tParsing tokens...')

        # parse() will be initiated automatically once initialised
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
                    '"-" found in {}. Name of propositions are assumed to be True, and no polarity sign is need!'.format(p))
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
        # premises
        # exceptions
        # conclusion
        # weight
        for arg_id in p.argument.children:
            # iterating through the each node of argument
            assert type(arg_id) is Node  # typecheck

            premise = set(arg_id.find_child('premise').children)
            exception = set(arg_id.find_child('exception').children)
            conclusion = arg_id.find_child('conclusion').children[0].data
            weight = float(arg_id.find_child('weight').children[0].data)

            # check the weight
            if weight < 0 or weight > 1:
                raise ValueError(
                    'weight for {} ({}) is not in range [0,1]'.format(
                        arg_id, weight))
            else:
                # store the weight in the dictionary for CAES
                self.caes_weight[arg_id] = weight

            # check that the literals are in the PROPOSITION.
            # the checker returns the PropLiteral, so there's no need to
            # convert it again
            ok_c, conclusion = self.check_prop(
                self.caes_propliteral, conclusion)
            ok_e, exception = self.check_prop(
                self.caes_propliteral, exception)
            ok_p, premise = self.check_prop(
                self.caes_propliteral, premise)

            if ok_c and ok_e and ok_p:
                # store the arguments
                self.caes_argument[arg_id] = \
                    Argument(conclusion=conclusion,
                             premises=premise,
                             exceptions=exception,
                             weight=weight,
                             arg_id=arg_id)

                # add to argset, the state of the argument is treated as None
                # when it is added
                self.argset.add_argument(
                    self.caes_argument[arg_id])

        # -----------------------------------------------------------------
        logging.info('\tAdding parameter to CAES')

        for param in p.parameter.children:
            if param.data == 'alpha':
                self.caes_alpha = float(param.children[0].data)
                # check that they are within range
                if self.caes_alpha > 1 or self.caes_alpha < 0:
                    raise ValueError(
                        'alpha must be within the range of 0 and 1 inclusive. {} given'.format(self.caes_alpha))

            elif param.data == 'beta':
                self.caes_beta = float(param.children[0].data)
                if self.caes_beta > 1 or self.caes_beta < 0:
                    raise ValueError(
                        'beta must be within the range of 0 and 1 inclusive. {} given'.format(self.caes_beta))

            elif param.data == 'gamma':
                self.caes_gamma = float(param.children[0].data)
                if self.caes_gamma > 1 or self.caes_gamma < 0:
                    raise ValueError(
                        'gamma must be within the range of 0 and 1 inclusive. {} given'.format(self.caes_gamma))

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

        # -----------------------------------------------------------------
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
        # Create file specific directory
        dot_dir = '../../dot/{}/'.format(
            path_to_file.split('/')[-1][:-4])  # remove the `.yml` extension too
        g_dir = '../../graph/{}/'.format(
            path_to_file.split('/')[-1][:-4])

        if not os.path.exists(dot_dir):
            os.makedirs(dot_dir)
        if not os.path.exists(g_dir):
            os.makedirs(g_dir)

        if not dialogue:  # dialogue == False
            # define the filename for write_to_graphviz
            dot_filename = dot_dir + 'full.dot'
            g_filename = g_dir + 'full.pdf'
            logging.info('\tInitialising CAES')
            self.run(g_filename, dot_filename)
            return

        elif dialogue:
            print('dialogue mode on')

            # Go through each issue and generate the dialogue
            for i, issue in enumerate(self.caes_issue):
                # define the filename for write_to_graphviz
                dot_filename = dot_dir + '{}_'.format(i + 1)
                g_filename = g_dir + '{}_'.format(i + 1)
                logging.info(
                    '=========================================\n\nISSUE: "{}"'.format(issue))
                # always starts from turn 0
                self.dialogue(issue, g_filename, dot_filename)
            return

        else:
            raise ValueError('Argument dialogue takes only boolean value')

    def run(self, g_filename, dot_filename, argset=None):
        """
        The standard output for CAES on the issues

        :param g_filename : the filename for the pycairo graph
        :param dot_filename : the filename for graphviz dot
        :param argset : optional to not use the argset created from the load function in Reader()
        """
        # ------------------------------------------------------------
        #       draw the argument graphs:
        # ------------------------------------------------------------
        if argset is None:
            argset = self.argset
        argset.draw(g_filename)
        argset.write_to_graphviz(dot_filename)

        # ------------------------------------------------------------
        #       Evaluate the issues using CAES
        # ------------------------------------------------------------
        caes = CAES(argset=argset,
                    audience=Audience(
                        self.caes_assumption, self.caes_weight),
                    proofstandard=ProofStandard(self.caes_proofstandard),
                    alpha=self.caes_alpha,
                    beta=self.caes_beta,
                    gamma=self.caes_gamma)

        for issue in self.caes_issue:
            logging.info(
                '\n\nEvaluating issue: {}'.format(issue))
            # use the aceptablility standard in CAES
            acceptability = caes.acceptable(issue)
            logging.info('------ {} {} acceptable ------'.format(
                issue, ['IS NOT', 'IS'][acceptability]))
            print('\n------ {} {} acceptable ------'.format(
                issue, ['IS NOT', 'IS'][acceptability]))

    # @TraceCalls()
    def dialogue(self, issue, g_filename, dot_filename, turn_num=None, argset=None):
        """
        1. Keeps track of the dialogue status for the issue - and output it
        when the dialogue is futile - `summary`
        2. For each proponent and opponent at every start of the turn find the
        'best argument to attack' each other.
        3. Once the party has presented their argument(s) and the Burden of
        Proof has been met, the process will repeat for the next party
        4. all these terminates when:
            a) there are no more arguments defined, OR
            b) there are no more "best arguments" by either party to attak each
            other - i.e. reached a stalemate
        5. When termination happens:
            a) the summary will be printed,
            b) with the acceptability of the issue evaluated using the PS
            defined by the users
        6) At each step of the argument, the status of the argument set will be
        printed, and the current view of the arguments (in an argumentation
        graph will be printed)

        :param issue : the issue :type PropLiteral that the propnent and opponent are arguing about
        :param g_filename : the filename for the graph to be drawn.
            For each state in a dialogue, a graph will be output.
        :param dot_filename : the filename for the dot file.
            For each state in a dialogue, a dot file will be ouput

        :return summary: the dialogue traces
        :return dialogue_state_argset: the argset of the dialogue
        """
        # Set up the arena:
        summary = ""
        ps_SE = ProofStandard([])  # use scintilla of evidence for every step
        if turn_num is None:
            # always starts with the proponent
            turn = 0
        else:
            turn = turn_num

        if argset is None:
            # create the argset for the dialogue
            dialogue_state_argset = ArgumentSet()
        else:
            dialogue_state_argset = argset

        # the arguments pro p; where p is the issue
        # sort the arguments according to their weight, with the largest first
        args_pro = self.argset.get_arguments(issue)
        args_pro = sorted(args_pro, key=lambda args: args.weight)
        best_arg = args_pro.pop()  # the argument with the largest weight
        # start with the best pro argument
        dialogue_state_argset.add_argument(best_arg,
                                           state='claimed')
        burden_status = self.burden_met(
            issue, dialogue_state_argset, ps_SE, turn)
        summary += self.dialogue_state(dialogue_state_argset,
                                       turn, burden_status,
                                       g_filename, dot_filename)

        # check that there are more arguments to be added into the argset
        while self.debatable(dialogue_state_argset):

            # the proponent's Burden of proof must first be met; otherwise she
            # has lost the argument
            if not burden_status:
                # need to further support premises:
                dialogue_state_argset = self.support_premise(
                    best_arg, dialogue_state_argset)
                # check if the burden is met
                burden_status = self.burden_met(
                    issue, dialogue_state_argset, ps_SE, turn)
                summary += self.dialogue_state(dialogue_state_argset,
                                               turn, burden_status,
                                               g_filename, dot_filename)

                # proponent cant satisfy the Burden
                if not burden_status:
                    logging.info(
                        "{} did not manage to satisfy her burden of proof".format(self.actors[turn % 2]))
                    logging.info('DIALOGUE ENDED')
                    logging.info('{}'.format(summary))
                    break

            # it is the Opponent's turn now:
            turn += 1  # next actor on the issue:

            # -------------------------------------------------------------
            # PROPONENT
            # -----------------------------------------------------------
            if turn % 2 == 0:
                # the argument with the largest weight
                # arg_pro = self.find_best_pro_argument(
                #     dialogue_state_argset)
                # # start with the best pro argument
                # dialogue_state_argset.add_argument(
                #     arg_pro, state='claimed')
                burden_status = self.burden_met(
                    issue, dialogue_state_argset, ps_SE, turn)
                summary += self.dialogue_state(dialogue_state_argset,
                                               turn, burden_status,
                                               g_filename, dot_filename)
                break

            # -----------------------------------------------------------
            # OPPONENT
            # -----------------------------------------------------------
            else:
                # start with the best con argument
                try:
                    (arg_con, arg_attacked) = self.find_best_con_argument(
                        dialogue_state_argset)
                except TypeError:
                    logging.info('Opponent is done here')
                    return

                # change the state of atgument to `questioned`
                dialogue_state_argset.set_argument_status(
                    argument_id=arg_con.arg_id, state='questioned')
                dialogue_state_argset.add_argument(
                    arg_con, state='claimed')
                burden_status = self.burden_met(
                    issue, dialogue_state_argset, ps_SE, turn)
                summary += self.dialogue_state(dialogue_state_argset,
                                               turn, burden_status,
                                               g_filename, dot_filename)
                continue

        # ----------------------------------------------------------------
        #   NO LONGER DEBATABLE:
        # ----------------------------------------------------------------
        g_file = g_filename + 'final.pdf'
        dot_file = dot_filename + 'final.dot'
        # Do acceptability test using the the PS defined:
        # self.run(g_filename=g_file, dot_filename=dot_file,
                #  argset=dialogue_state_argset)
        logging.info('{}'.format(summary))  # summarise the dialogue
        return summary, dialogue_state_argset

    def debatable(self, dialogue_state_argset):
        """
        Given the current dialogue state, check if there are any more arguments to be added

        :param dialogue_state_argset - the current state for the dialogue
        :rtype True - if there are more arguments to be added; otherwise False
        """

        print('Checking debatable..?')
        # arg_pro = self.find_best_pro_argument(dialogue_state_argset)
        # arg_con = self.find_best_con_argument(dialogue_state_argset)
        # if len(arg_pro + arg_con):
        #     logging.debug('Checking if debatable... True')
        #     return True
        # else:
        delta = [
            x for x in dialogue_state_argset.arguments if x not in self.argset.arguments]
        if len(delta):
            # the number of arguments have been maxed out!
            logging.info(
                'All arguments have been added into the argset! nothing else to consider')
            logging.debug('Checking if debatable... False')
            return False
        else:
            return True

    def support_premise(self, current_arg, argset):
        """
        Since the proponent of the argument have the burden of production for
        its premises, this function models the proponent trying to support
        their argument by finding additional arguments that can support the
        premise.

        :param current_arg : :type Argument - the argument that that needs to be support in the curent argset
        :param argset : the current dialogue state argset where new arguments should be added
        """
        logging.info('Supporting premises for arg: {}'.format(current_arg))
        for premise in current_arg.premises:
            # find arguments to support the premises
            for args in self.argset.get_arguments(premise):
                argset.add_argument(args, state='claimed')
        return argset

    def burden_met(self, issue, argset, ps, turn_num):
        """
        Checks that the burden of proof of the proponent or opponent is met
        using the CAES acceptability function.
        If it is acceptable, the party have met its burden of proof.

        :param argset: the current arguments that are being considered
        :param ps : proofstandard for the arguments. If ps is an empty list,
        then the default scintilla of evidence is used for all the statement.
        """
        caes = CAES(argset=argset,
                    proofstandard=ps,
                    audience=Audience(
                        self.caes_assumption, self.caes_weight),
                    alpha=self.caes_alpha,
                    beta=self.caes_beta,
                    gamma=self.caes_gamma)
        burden_status = caes.acceptable(issue)
        print("\n-----------------------------------------\nBurden of Proof met by {} : {}".format(
            self.actors[turn_num % 2], burden_status) + "\n-----------------------------------------")

        return burden_status

    def find_best_pro_argument(self, argset):
        """
        find the best argument to attack the current arguments put forth by the opponent
        """
        full_argset = self.argset

    def find_best_con_argument(self, argset):
        """
        The respondent to the argument have the burden of production of any
        exceptions. First, we find the list of claims put forth by the
        proponent. If there are multiple claims, we rank the claims according
        to their weights.

        For each claim:
        1) check if there are exceptions
            2) for each exceptions, check if there are arguments that will lead
            to the exception being true
            3) return the argument with the highest weight

        if there are NO argument to support the exceptions in the claims, then
        we have to find a rebuttal to the claims
        This is done as:
        1) find any argument that is `con` of the claim (start finding )
        """
        # first, find the arguments that are claimed by the proponent, and sort
        # it according to their weight
        args_claimed = argset.get_arguments_status('claimed')
        args_claimed = sorted(args_claimed, key=lambda arg: arg.weight)

        while len(args_claimed):

            arg = args_claimed.pop()  # the argument with the hgihest weightage
            if len(arg.exceptions):  # if there are exceptions
                for exception in arg.exceptions:
                    # iterate through the exceptions and find arguments that
                    # can be used to claim the exceptions
                    args_con = self.argset.get_arguments(exception)
                    if len(args_con):
                        args_con = sorted(args_con, key=lambda arg: arg.weight)
                        # return the argument that supports the exception with the
                        # largest weight and the argument this argument is attacking
                        return (args_con.pop(), arg)

            else:
                # consider the next claim by the proponent
                continue

        # if ever reached here, there are no arguments to attacked the
        # exceptions. Hence, a rebuttal is needed
        while len(args_claimed):
            arg = args_claimed.pop()

            arg_con = self.argset.get_arguments_con(arg.conclusion)

            if len(arg_con):
                # there';s at least one argument that is avaliable for rebuttal
                arg_con = sorted(arg_con, key=lambda arg: arg.weight)
                return (arg_con.pop(), arg)

            else:
                # consider the net claim by proponent
                continue

        return False

    def dialogue_state(self, argset, turn_num, burden_status, g_filename, dot_filename):
        """
        1) print and log the current dialogue status
        2) output the graph for viewing at this turn!
        """

        # CURRENT STAUS
        logging.info(
            '================== turn {} =================='.format(turn_num))
        summary = '================== turn {} =================='.format(
            turn_num) + '\n'
        # print Where the BOP lies in for this turn
        logging.info('BURDEN OF PROOF @ {}'.format(self.actors[turn_num % 2]))
        summary += 'BURDEN OF PROOF @ {}'.format(
            self.actors[turn_num % 2]) + '\n'

        #  ARGUMENTS
        logging.info('ARGUMENTS:')
        summary += 'ARGUMENTS:\n'
        for arg in argset.arguments:
            logging.info(arg.__str__())
            summary += arg.__str__() + '\n'

        logging.info("\n-----------------------------------------\nBurden of proof met by {} : {}".format(
            self.actors[turn_num % 2], burden_status) + "\n-----------------------------------------")
        summary += ("\n-----------------------------------------\nBurden of proof met by {} : {}".format(
            self.actors[turn_num % 2], burden_status) + "\n-----------------------------------------\n")
        # GRAPHS
        g_file = g_filename + str(turn_num) + '.pdf'
        dot_file = dot_filename + str(turn_num) + '.dot'
        argset.draw(g_file)
        argset.write_to_graphviz(dot_file)
        logging.info(
            '================== turn {} =================='.format(turn_num))
        summary += '============================================'.format(
            turn_num) + '\n\n'
        return summary

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
                yes, prop = self.check_prop(caes_propliteral, p)
                checker = checker and yes  # if no, the function would already had raised an error
                set_props.add(prop)

            return checker, set_props

        elif type(prop_id) is str:
            negate = 0  # check for negation first
            if prop_id[0] == '-':
                prop_id = prop_id[1:]
                negate = 1

            if prop_id not in caes_propliteral.keys():  # throw error if the key doesnt exists in the dictionary
                raise ValueError(
                    '"{}" is not defined in PROPOSITION'.format(prop_id))
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
        standards = {'scintilla': "scintilla",
                     'preponderance': "preponderance",
                     'clear and convincing': "clear_and_convincing",
                     'beyond reasonable doubt': "beyond_reasonable_doubt",
                     'dialectical validitys': "dialectical_validity"}

        if query in standards.keys():
            return True, standards[query]
        else:
            raise ValueError(
                'Invalid proof standard "{}" found'.format(query))

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

    def __init__(self, conclusion, premises=set(), exceptions=set(), weight=0, arg_id=None):
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

    def add_proposition(self, proposition):
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
                logging.debug(
                    "Proposition '{}' is already in graph".format(proposition))
            else:
                # add the proposition as a vertex attribute, recovered via the
                # key 'prop'
                self.graph.add_vertex(prop=proposition)
                logging.debug(
                    "Added proposition '{}' to graph".format(proposition))
            # return the vertex
            return self.graph.vs.select(prop=proposition)[0]

        else:
            raise TypeError('Input {} should be PropLiteral'.
                            format(proposition))

    def add_argument(self, argument, state=None):
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
        self.arguments.append(argument)  # store a list of arguments
        # -----------------------------------------------------------
        #   VERTICES
        # -----------------------------------------------------------
        # add the arg_id as a vertex attribute, recovered via the 'arg' key
        if state is not None:
            assert state == 'claimed' or state == 'questioned'
        self.graph.add_vertex(arg=argument.arg_id, state=state)
        # returns the vertex that goes to the argument
        arg_v = g.vs.select(arg=argument.arg_id)[0]
        # add proposition vertices to the graph
        # conclusion:
        conclusion_v = self.add_proposition(argument.conclusion)
        self.add_proposition(argument.conclusion.negate())
        # premise:
        premise_vs = [self.add_proposition(prop)
                      for prop in sorted(argument.premises)]
        # exception:
        exception_vs = [self.add_proposition(prop)
                        for prop in sorted(argument.exceptions)]
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

    def get_argument_exceptions(self, argument_id):
        """
        given an arg_id, find the exceptions in that argument.
        If no exceptions are found, return None

        :param: argument_id: The argument_id of interest
        :return: A proposition that are exceptions of the argument
        :rtype: list(:class:`PropLiteral`)
        """
        for arg in self.arguments:
            if arg.arg_id == argument_id:
                return sorted(arg.exceptions)

        raise ValueError(
            'No {} found in arguments in argset'.format(argument_id))

    def get_arguments_con(self, proposition):
        """
        Given a proposition p, use get_arguments to find the arguments that are are con p

        :param proposition: The proposition to checked.
        :type proposition: :class:`PropLiteral`
        """
        return self.get_arguments(proposition.negate())

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

    def get_arguments_status(self, status):
        """
        Find the arguments with the desired attribute value

        :param status - a member {claimed, questioned}
        :raise ValueError if the status is not of claimed or questioned
        """
        if str(status) != 'claimed' and str(status) != 'questioned':
            raise ValueError('{} is not a valid status'.format(status))
        else:
            arg_IDs = [self.graph.vs[v.index]['arg']
                       for v in self.graph.vs.select(state=status)]
            args = [arg for arg in self.arguments if arg.arg_id in arg_IDs]
            return args

    def set_argument_status(self, argument_id, state):
        """
        Update the status of an argument to either {claimed, questioned}
        """
        arg_v = self.graph.vs.select(arg=argument_id)
        self.graph.vs.select(arg=argument_id)['state'] = state
        print(self.graph)

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
        for x in g.vs['arg']:
            if x is None:  # if it is an arguments
                plot_style['vertex_color'].append('lightblue')
            else:
                # darker red = larger weight
                how_red = [1, 1 - self.arguments[counter].weight, 0.5]
                plot_style['vertex_color'].append(how_red)
                counter += 1
        plot_style['vertex_shape'] = \
            ['circular' if x is None else 'rect' for x in g.vs['arg']]
        plot_style['vertex_size'] = 30
        # use thicker lines if the node is an exception of the argument
        plot_style["edge_width"] = [
            1 + 2 * int(is_exception) for is_exception in g.es["is_exception"]]
        # rotation, 0 is right of the vertex
        plot_style['vertex_label_angle'] = 1.5
        plot_style['vertex_label_dist'] = -2
        # plot_style['vertex_label_size'] = 20
        # General plot
        plot_style['margin'] = (100, 100, 100, 100)  # pixels of border
        plot_style['bbox'] = (800, 600)  # change the size of the image
        plot_style['layout'] = layout
        # execute the plot
        plot(g, g_filename, autocurve=True, **plot_style)

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
                result += '"{}" -> "{}" [arrowhead=dot]'.format(
                    source_label, target_label)
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
        self.proof_standards = ["scintilla", "preponderance",
                                "clear_and_convincing",
                                "beyond_reasonable_doubt",
                                "dialectical_validity"]
        self.default = default
        self.config = defaultdict(lambda: self.default)
        self._set_standard(propstandards)

    def _set_standard(self, propstandards):
        for (prop, standard) in propstandards:
            if standard not in self.proof_standards:
                raise ValueError("{} is not a valid proof standard".
                                 format(standard))
            self.config[prop] = standard

    def get_proofstandard(self, proposition):
        """
        Determine the proof standard associated with a proposition.

        :param proposition: The proposition to be checked.
        :type proposition: :class:`PropLiteral`
        """
        return self.config[proposition]


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

    def __init__(self, argset, audience, proofstandard, alpha=0.4, beta=0.3,
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
        logging.debug(
            'Checking applicability of {}...'.format(argument.arg_id))
        logging.debug('Current assumptions: {}'.format(self.assumptions))
        logging.debug('Current premises: {}'.format(argument.premises))

        # Checking the applicablility of the premises
        #
        b1 = all(p in self.assumptions or
                 (p.negate() not in self.assumptions and
                  _acceptable(p)) for p in argument.premises)

        #  Checking applicablility of exceptions
        if argument.exceptions:
            logging.debug('Current exception: {}'.format(argument.exceptions))
        b2 = all(e not in self.assumptions and
                 (e.negate() in self.assumptions or
                  not _acceptable(e)) for e in argument.exceptions)

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
        logging.debug("Checking whether proposition '{}'"
                      "meets proof standard '{}'.".
                      format(proposition, standard))
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
            logging.debug("max weight pro '{}' >  alpha '{}': {}".
                          format(mwp, self.alpha, exceeds_alpha))
            logging.debug("diff between pro and con = {} > gamma: {}".
                          format(mwp - mwc, diff_exceeds_gamma))

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
            raise ValueError("No weight assigned to argument '{}'.".
                             format(arg_id))

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
        logging.debug('Checking applicability and weights of {}'.
                      format(applic_arg_ids))
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
        argparser.add_argument('pathname',
                               nargs='+',
                               default='"../../samples/example.yml"',
                               help='path to each of your .yml file(s). At least one must be given (example: %(default)s)')
        argparser.add_argument('-d', '--dialogue',
                               dest='dialogue',
                               help='shows the shifting burden of proof while the arguments are evaluated in CAES. If the flag is used, dialogue mode will be used for all the files',
                               action='store_true')
        argparser.add_argument('-logger',
                               dest='logger',
                               help='logging level (default: %(default)s)',
                               choices=['DEBUG', 'INFO'],
                               default='DEBUG',
                               type=str,
                               action='store')
        argparser.add_argument('-buffer', '--buffer_size',
                               dest='buffer_size',
                               help='set the buffer size of the reader (default: %(default)s)',
                               required=False,
                               action='store',
                               default=4096,
                               type=int)
        argparser.add_argument('-indent', '--indent_size',
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
                'You have given a directory!\nUsage: $ python caes.py path_to_file | [path_to_file]+')
            exit()

        elif len(filenames) > 1:  # if user gave a list of filenames
            # inform the number of files
            print('{} files detected'.format(len(filenames)))

            for filename in filenames:
                logger_file = '../../log/{}.log'.format(
                    filename.split('/')[-1])
                logging.basicConfig(format='%(message)s',
                                    level=args['logger'],
                                    filemode='w',
                                    filename=logger_file)

                # check that the filename parsed are all files
                assert os.path.isfile(filename), logging.exception(
                    '{} is not a file'.format(filename))
                print('\nProcessing {}'.format(filename))

                Reader(buffer_size=args['buffer_size'], indent_size=args['indent_size']).load(
                    filename, dialogue=args['dialogue'])

                logger = logging.getLogger()
                logger.removeHandler(logger.handlers[0])

        else:  # Support if user gives a directory instead of a list of filename
            if os.path.isfile(file_check):
                logger_file = '../../log/{}.log'.format(
                    file_check.split('/')[-1])
                logging.basicConfig(format='%(message)s',
                                    level=args['logger'],
                                    filemode='w',
                                    filename=logger_file)

                # check that the filename parsed are all files
                assert os.path.isfile(file_check), logging.exception(
                    '{} is not a file'.format(filename))
                print('\nProcessing {}'.format(file_check))

                Reader(buffer_size=args['buffer_size'], indent_size=args['indent_size']).load(
                    file_check, dialogue=args['dialogue'])

            else:
                logging.error('Cannot find file {}'.format(filenames))
                exit()
