"""
Implementation of the Dialogue for the arguments
"""

import logging
from caes import CAES

class Dialogue(object):
    """
    Dialogue simulates the conversation between the proponent and opponent in
    the courthouse
    """

    def __init__(self, issue, caes_argset, caes_weight, dot_filename,
                 g_filename, run):
        """
        """
        self.actors = ['PROPONENT', 'RESPONDENT']
        self.dot_filename = dot_filename
        self.g_filename = g_filename
        self.top_issue = issue
        self.caes_weight = caes_weight
        self.argset = caes_argset
        self.run = run

        # -----------------------------------------------------------------
        # RUN the dialogue
        # -----------------------------------------------------------------
        dialogue_state_argset, summary, turn_num = \
            self.dialogue(self.top_issue, self.g_filename, self.dot_filename)
        logging.info(
            '\n\n\n********************************************************************************'
        )
        logging.info(
            'DIALOGUE SUMMARY:\n********************************************************************************\n{}'.
            format(summary))
        logging.info(
            '********************************************************************************'
        )

    # @TraceCalls()
    def dialogue(self,
                 issue,
                 g_filename,
                 dot_filename,
                 turn_num=None,
                 dialogue_state_argset=None,
                 summary=None):
        """
        ** In dialogue, the proponent and respondent of the issue is not the
        same as the proponent (such as prosecution) and opponent (such as
        defendant) in the setting. A proponent to the issue can be the
        defendant, and the respondent will hence be the prosecutor. This is modelled in this function as the turn_num. A odd turn number is the proponent of the issue, and the even the respondent.

        This function:
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

        # -----------------------------------------------------------------
        # Set up the arena:
        # -----------------------------------------------------------------
        ps_SE = ProofStandard([])  # use scintilla of evidence for BOP checking
        if summary is None:
            summary = ""
        if turn_num is None:
            turn_num = 0  # always starts with the proponent
        if dialogue_state_argset is None:
            dialogue_state_argset = ArgumentSet()  # store the dialogue

        # -----------------------------------------------------------------
        # Start the dialogue by finding the best pro argument by the proponent
        # -----------------------------------------------------------------
        args_pro = self.argset.get_arguments(issue)
        try:
            args_pro_dialogue = dialogue_state_argset.get_arguments(issue)
            args_pro = [
                arg for arg in args_pro if arg not in args_pro_dialogue
            ]
        except KeyError:
            pass

        # start with the best argument, i.e. the one with the highest weight
        args_pro = sorted(args_pro, key=lambda args: args.weight)
        try:
            best_arg_pro = args_pro.pop()
        except IndexError:
            # If the argument cannot be reached as there is nothing to argue
            # about, then we will just evaluate it according to the full
            # argumentaion set available.
            g_file = g_filename + 'final.pdf'
            dot_file = dot_filename + 'final.dot'
            logging.info(
                'ISSUE "{}" cannot be evaluated because there are insufficient arguments to form an argumentation graph'.
                format(issue))
            logging.info('Evaluating on the full argumentation set')
            self.run(issues=issue, g_filename=g_file, dot_filename=dot_file)
            return dialogue_state_argset, summary, turn_num

        # Add the first argument pro the issue into the argset:
        dialogue_state_argset.add_argument(
            best_arg_pro, state='claimed', claimer=self.actors[turn_num % 2])
        summary += self.dialogue_state(dialogue_state_argset, issue, turn_num,
                                       '?', g_filename, dot_filename)

        # check that the proponent of issue have met her burden of proof
        # The evaluation of the Burden of Proof is using scintilla of evidence
        dialogue_state_argset, summary, burden_status = \
            self.burden_met(issue, best_arg_pro,
                            dialogue_state_argset, ps_SE, turn_num, summary)

        summary += self.dialogue_state(dialogue_state_argset, issue, turn_num,
                                       burden_status, g_filename, dot_filename)
        # the proponent's Burden of proof must first be met; otherwise she
        # has lost the argument
        # TODO: TEST WHAT IF DOWNSTREAM THE BURDEN OF PROOF IS NOT SATISFIABLE?
        if not burden_status:
            logging.info('{} did not met the Burden of Proof for issue \'{}\''.
                         format(self.actors[turn_num % 2], issue))
            # raise Exception("Burden of Proof not met!")
            return dialogue_state_argset, summary, turn_num

        else:

            # the respondent turn's to raise an issue
            turn_num += 1

            try:
                (arg_con, arg_attacked) = \
                    self.find_best_con_argument(
                        issue, dialogue_state_argset)
            except TypeError:
                logging.info('No arguments found by {} for issue \'{}\''.
                             format(self.actors[turn_num % 2], issue))
                return dialogue_state_argset, summary, turn_num

            # if there's a arg_con found, create a issue to be debated
            dialogue_state_argset.set_argument_status(
                concl=arg_attacked.conclusion, state='questioned')
            sub_issue = arg_con.conclusion
            logging.info('SUB ISSUE: "{}"'.format(sub_issue))
            dialogue_state_argset, summary, turn_num = \
                self.dialogue(sub_issue, g_filename, dot_filename,
                              turn_num, dialogue_state_argset, summary)
            summary += self.dialogue_state(dialogue_state_argset, issue,
                                           turn_num, burden_status, g_filename,
                                           dot_filename)
        # ----------------------------------------------------------------
        #   NO LONGER DEBATABLE?
        # ----------------------------------------------------------------
        g_file = g_filename + 'final.pdf'
        dot_file = dot_filename + 'final.dot'
        # Do acceptability test using the the PS defined:
        acceptability = self.run(g_filename=g_file,
                                 dot_filename=dot_file,
                                 argset=dialogue_state_argset,
                                 issues=[issue])

        while not acceptability:
            if len(args_pro):
                # If there are other arguments that can help with the issue,
                # add them in:
                dialogue_state_argset, summary, turn_num = \
                    self.dialogue(issue, g_filename, dot_filename,
                                  turn_num, dialogue_state_argset, summary)
                acceptability = self.run(g_filename=g_file,
                                         dot_filename=dot_file,
                                         argset=dialogue_state_argset,
                                         issues=issue)
            else:
                logging.info('No arguments found')
                return dialogue_state_argset, summary, turn_num

        return dialogue_state_argset, summary, turn_num

    def burden_met(self, issue, argument, argset, ps, turn_num, summary):
        """
        Checks that the burden of proof of the proponent or opponent is met
        using the CAES acceptability function. If it is not met, try to find
        support for the premises, and adding them to the argset.

        :param argset: the current arguments that are being considered
        :param ps : proofstandard for the arguments. If ps is an empty list,
        then the default scintilla of evidence is used for all the statement.
        """
        logging.info('Checking burden of proof for {}'.format(self.actors[
            turn_num % 2]))
        caes = CAES(
            argset=argset,
            proofstandard=ps,
            audience=Audience(self.caes_assumption, self.caes_weight))
        burden_status = caes.acceptable(issue)
        logging.debug("CHECKING THE BURDEN OF PROOF")

        # if the burden is not met due to the premises not supported,
        # find arguments to support the premises
        if not burden_status:
            for premise in argument.premises:
                # find arguments that support the premises
                for arg in self.argset.get_arguments(premise):
                    try:
                        # prevent repeated argument from being added into
                        # argset
                        argset.add_argument(
                            arg,
                            state='claimed',
                            claimer=self.actors[turn_num % 2])
                        argset.set_argument_status(
                            arg.conclusion, state='claimed')
                    except ValueError:
                        return argset, summary, False

            # Check if the burden is met after adding the arguments
            # to support the premises
            logging.debug('HAHSDHASDHASHDASHASDH')
            argset, summary, burden_status = \
                self.burden_met(issue, argument, argset, ps, turn_num, summary)

            # proponent cant satisfy the Burden
            if not burden_status:
                logging.info(
                    "{} did not manage to satisfy her burden of proof".format(
                        self.actors[turn_num % 2]))
                logging.info('{}'.format(summary))

        return argset, summary, burden_status

    def find_best_con_argument(self, issue, argset):
        """
        The respondent to the argument have the burden of production of any
        exceptions. First, we find the list of claims put forth by the
        proponent. If there are multiple claims, we rank the claims according
        to their weights. For each claim:
        1) check if there are exceptions
            2) for each exceptions, check if there are arguments that will lead
            to the exception being true
            3) return the argument with the highest weight

        if there are NO argument to support the exceptions in the claims, then
        we have to find a rebuttal to the claims
        This is done as:
        1) find any argument that is `con` of the claim
        """
        # first, find the arguments that are claimed by the proponent, and sort
        # it according to their weight
        args_claimed_ = argset.get_arguments_status(issue, 'claimed')
        args_claimed_sorted = sorted(args_claimed_, key=lambda arg: arg.weight)

        while len(args_claimed_sorted):
            # the argument with the hgihest weightage
            arg = args_claimed_sorted.pop()
            if len(arg.exceptions):  # if there are exceptions
                for exception in arg.exceptions:
                    # iterate through the exceptions and find arguments that
                    # can be used to claim the exceptions
                    args_con = self.argset.get_arguments(exception)
                    if len(args_con):
                        args_con = sorted(args_con, key=lambda arg: arg.weight)
                        # return the argument that supports the exception with the
                        # largest weight and the argument this argument is
                        # attacking
                        return (args_con.pop(), arg)
            else:
                # consider the next claim by the proponent
                continue

        # if ever reached here, there are no arguments to attacked the
        # exceptions. Hence, a rebuttal is needed
        args_claimed_sorted = sorted(args_claimed_, key=lambda arg: arg.weight)
        while len(args_claimed_sorted):
            arg = args_claimed_sorted.pop()
            arg_con = self.argset.get_arguments_con(arg.conclusion)
            if len(arg_con):
                # there';s at least one argument that is avaliable for rebuttal
                arg_con = sorted(arg_con, key=lambda arg: arg.weight)
                return (arg_con.pop(), arg)
            else:
                # consider the net claim by proponent
                continue

        return False

    def dialogue_state(self,
                       argset,
                       issue,
                       turn_num,
                       burden_status,
                       g_filename=None,
                       dot_filename=None):
        """
        1) print and log the current dialogue status
            - Which party have the burden of proof
            - the arguments in the current state
            - satisfiability of the burden of proof by the actor
            - the acceptability of the top level issue at the curent level
        2) output the graph for viewing at this turn!
        """

        # CURRENT STAUS
        logging.info('================== turn {} =================='.format(
            turn_num))
        summary = '================== turn {} =================='.format(
            turn_num) + '\n'
        # print Where the BOP lies in for this turn
        logging.info('BURDEN OF PROOF @ {}'.format(self.actors[turn_num % 2]))
        summary += 'BURDEN OF PROOF @ {}'.format(self.actors[turn_num %
                                                             2]) + '\n'

        #  ARGUMENTS
        logging.info('ARGUMENTS:')
        summary += 'ARGUMENTS:'
        for arg in argset.arguments:
            logging.info(arg.__str__())
            summary += '\n' + arg.__str__()

        logging.info(
            "-----------------------------------------\nBurden of proof met by {} : {}".
            format(self.actors[turn_num % 2], burden_status))
        summary += (
            "\n-----------------------------------------\nBurden of proof met by {} : {}".
            format(self.actors[turn_num % 2], burden_status))

        # Top issue acceptable??
        logging.info('-----------------------------------------')
        ps = []  # store all the relevant proofstandard
        for arg in argset.arguments:
            # iterate through the arguments, and find the proofstandard used to
            # evaluate the conclusion of these arguments from proofstandards
            # parsed
            concl = arg.conclusion
            ps.extend([(prop_id, prop_ps)
                       for (prop_id, prop_ps) in self.caes_proofstandard
                       if prop_id == concl])
        logging.debug(ps)
        ps = ProofStandard(ps)
        acceptability = self.run(argset=argset, issues=issue, proofstandard=ps)
        summary += (
            "\n-----------------------------------------\n\t\tISSUE \"{}\" acceptable? -> {}".
            format(issue, acceptability))

        if self.top_issue != issue:
            acceptability_top = self.run(argset=argset,
                                         issues=self.top_issue,
                                         proofstandard=ps)
            summary += ("\nTOP ISSUE \"{}\" acceptable? -> {}".format(
                self.top_issue, acceptability_top))

        # GRAPHS
        if g_filename is not None and dot_filename is not None:
            g_file = g_filename + str(turn_num) + '.pdf'
            dot_file = dot_filename + str(turn_num) + '.dot'
            argset.draw(g_file)
            argset.write_to_graphviz(dot_file)
        logging.info('============================================')
        summary += '\n============================================\n'
        return summary
