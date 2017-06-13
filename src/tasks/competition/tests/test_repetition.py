# -*- coding: utf-8
# 'version': '0.2'
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import unittest
import tasks.competition.repetition as repetition
import tasks.competition.messages as msg
from tasks.competition.tests.helpers import task_messenger


class TestRepetitionTasks(unittest.TestCase):
    """
    # helper methods
    """
    def check_positive_feedback(self, m, instructions, answer):
        """ # hear the congratulations  # there is some feedback

        :param m:
        :param instructions:
        :param answer:
        :return:
        """
        feedback_blen = m.read()
        self.assertGreater(feedback_blen, 0)
        m.send()
        self.assertEqual(m.get_cumulative_reward(), 1, "answering '{0}' to query '{1}' didn't work.".format(
                             answer, instructions))

    def check_negative_feedback(self, m, exp_answer):
        """# hear the feedback# if the correct message wasn't given, the feedback was an error message

        :param m:
        :param exp_answer:
        :return:
        """

        m.read()
        try:
            answer, = m.search_last_message(
                r"correct answer is: (.+)\.$")
            self.assertEqual(answer, exp_answer)
        except RuntimeError:
            self.assertIn(m.get_last_message(), msg.failed)

    def solve_correctly_test(self, m, get_correct_answer):
        """ # wait for the instructions# there are some instructions# repeat it

        :param m:
        :param get_correct_answer:
        :return:
        """
        instructions_blen = m.read()
        instructions = m.get_last_message()
        self.assertGreater(instructions_blen, 0)
        answer = get_correct_answer(m)
        m.send(answer + ".")
        self.check_positive_feedback(m, instructions, answer)

    def add_ending_garbage_test(self, m, get_correct_answer):
        """# wait for the instructions# there are some instructions# repeat it with some garbage at the end# hear
        feedback if there is any# stay silent until the end

        :param m:
        :param get_correct_answer:
        :return:
        """
        instructions_blen = m.read()
        self.assertGreater(instructions_blen, 0)
        answer = get_correct_answer(m)
        m.send(answer + " spam, spam, eggs, bacon and spam.")
        self.check_negative_feedback(m, answer)
        self.assertEqual(m.get_cumulative_reward(), 0, "The correct answer must be an exact match.")
        while m.is_silent():
            m.send()
        self.assertEqual(m.get_cumulative_reward(), 0, "The correct answer must be an exact match.")

    def timeout_test(self, m, get_correct_answer):
        """# read the instructions# get the answer# stay silent# hear the correction

        :param m:
        :param get_correct_answer:
        :return:
        """
        m.read()
        answer = get_correct_answer(m)
        while m.is_silent():
            m.send()
        self.check_negative_feedback(m, answer)
        self.assertEqual(m.get_cumulative_reward(), 0, "Doing nothing is not a solution")

    def repeat_everything(self, m, get_correct_answer):
        """# first, send one silence# repeat the previous char sent by the teacher# read feedback, if any

        :param m:
        :param get_correct_answer:
        :return:
        """
        m.send()
        while not m.is_silent():
            m.send(m.get_text()[-1])
        m.send(m.get_text()[-1])
        m.read()
        self.assertEqual(m.get_cumulative_reward(), 0, "Memory-less repeating cannot work")

    def do_test_battery(self, task, get_correct_answer):
        """# test for solving the task correctly# test for not solving it at all# test for not solving it at all#
        test for solving the task correctly

        :param task:
        :param get_correct_answer:
        :return:
        """
        with task_messenger(task) as m:
            self.solve_correctly_test(m, get_correct_answer)
        with task_messenger(task) as m:
            self.repeat_everything(m, get_correct_answer)
        with task_messenger(task) as m:
            self.add_ending_garbage_test(m, get_correct_answer)
        with task_messenger(task) as m:
            self.timeout_test(m, get_correct_answer)

"""
task testing routines
"""
    def testBeSilent(self):
        """# read the instructions# there are some instructions# stay silent until rewarded# read the instructions
        again# there are some instructions# we fail# we should have prompted a restart# there are some instructions

        :param self:
        :return:
        """
        with task_messenger(repetition.BeSilentTask) as m:
            instructions_blen = m.read()
            instructions = m.get_last_message()
            self.assertGreater(instructions_blen, 0)
            for x in range(1000):
                if m.get_cumulative_reward() > 0:
                    break
                m.send()
            self.assertEqual(m.get_cumulative_reward(), 1)
            instructions_blen = m.read()
            instructions = m.get_last_message()
            self.assertGreater(instructions_blen, 0)
            m.send('a')
            self.assertEqual(m.get_cumulative_reward(), 1)
            m.read()
            instructions = m.get_last_message()
            self.assertGreater(len(instructions), 0)
            self.assertEqual(m.get_cumulative_reward(), 1)

    def testRepeatCharacter(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """# get the string to be repeated# cannot use the add ending garbage test here (spam. could prompt a
            correct answer if the query is for m)# test for solving the task correctly# test for not solving it at all
            test for solving the task correctly

            :param m:
            :return:
            """
            answer, = m.search_last_message(r"(?:{verb}) (\w)\.".format(
                verb="|".join(repetition.verbs)))
            return answer
        task = repetition.RepeatCharacterTask
        with task_messenger(task) as m:
            self.solve_correctly_test(m, get_correct_answer)
        with task_messenger(task) as m:
            self.repeat_everything(m, get_correct_answer)
        with task_messenger(task) as m:
            self.timeout_test(m, get_correct_answer)

    def testRepeatWhatISay(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """# get the string to be repeated

            :param m:
            :return:
            """
            answer, = m.search_last_message(r"(?:{verb}) (.*)\.".format(verb="|".join(repetition.verbs)))
            return answer
        self.do_test_battery(repetition.RepeatWhatISayTask, get_correct_answer)

    def testRepeatWhatISay2(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """# get the string to be repeated

            :param m:
            :return:
            """
            answer, = m.search_last_message(r"(?:{verb}) (.*) (?:{context})\.".format(verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            return answer
        self.do_test_battery(repetition.RepeatWhatISay2Task, get_correct_answer)

    def testRepeatWhatISayMultipleTimes(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """# get the string to be repeated

            :param m:
            :return:
            """
            answer, n = m.search_last_message(r"(?:{verb}) (.*) (\w+) times\.".format(verb="|".join(repetition.verbs)))
            return " ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(repetition.RepeatWhatISayMultipleTimesTask, get_correct_answer)

    def testRepeatWhatISayMultipleTimes2(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """# get the string to be repeated

            :param m:
            :return:
            """
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times (?:{context})\.".format(verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            return " ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(repetition.RepeatWhatISayMultipleTimes2Task, get_correct_answer)

    def testRepeatWhatISayMultipleTimesSeparatedByComma(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """# get the string to be repeated

            :param m:
            :return:
            """
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times separated".format(verb="|".join(repetition.verbs),
                                                                context="|".join(repetition.context)))
            return ", ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(repetition.RepeatWhatISayMultipleTimesSeparatedByCommaTask, get_correct_answer)

    def testRepeatWhatISayMultipleTimesSeparatedByAnd(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """# get the string to be repeated

            :param m:
            :return:
            """
            answer, n = m.search_last_message(
                r"(?:{verb}) (.*) (\w+) times separated".format(verb="|".join(repetition.verbs),
                    context="|".join(repetition.context)))
            return " and ".join([answer] * msg.string_to_number(n))
        self.do_test_battery(repetition.RepeatWhatISayMultipleTimesSeparatedByAndTask, get_correct_answer)

    def testRepeatWhatISayMultipleTimesSeparatedByCA(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ get the string to be repeated

            :param m:
            :return:
            """

            answer, n = m.search_last_message(r"(?:{verb}) (.*) (\w+) times separated".format(
                verb="|".join(repetition.verbs), context="|".join(repetition.context)))
            enum = [answer] * msg.string_to_number(n)
            return " and ".join([", ".join(enum[:-1]), enum[-1]])
        self.do_test_battery(repetition.RepeatWhatISayMultipleTimesSeparatedByCATask, get_correct_answer)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
