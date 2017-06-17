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
from worlds.grid_world import GridWorld
import tasks.competition.messages as msg
import tasks.competition.navigation as navigation
import tasks.competition.repetition as repetition
from tasks.competition.tests.helpers import task_messenger


class TestNavigation(unittest.TestCase):
    """
    helper methods
    """
    def check_positive_feedback(self, m, instructions):
        """ hear the congratulations# there is some feedback

        :param m:
        :param instructions:
        :return:
        """
        feedback_blen = m.read()
        self.assertGreater(feedback_blen, 0)
        m.send()
        self.assertEqual(m.get_cumulative_reward(), 1)

    def check_negative_feedback(self, m):
        """# hear the feedback # it should be bad-learner sort of feedback

        :param m:
        :return:
        """
        m.read()
        feedback = m.get_last_message()
        self.assertTrue(feedback in msg.failed or feedback in msg.timeout,
                        'Unexpected negative feedback: {0}'.format(feedback))

    def solve_correctly_test(self, m, solve):
        """# read the instructions # get the instructions # solve the problem # hear the congratulations

        :param m:
        :param solve:
        :return:
        """
        m.read()
        instructions = m.get_last_message()
        solve(m)
        self.check_positive_feedback(m, instructions)

    def timeout_test(self, m, solve):
        """ # read the instructions # stay silent # hear the correction

        :param m:
        :param solve:
        :return:
        """
        m.read()
        while m.is_silent():
            m.send()
        self.check_negative_feedback(m)

    def do_test_battery(self, task, solve):
        """ # test for solving the task correctly # test for not solving it at all

        :param task:
        :param solve:
        :return:
        """
        with task_messenger(task, GridWorld) as m:
            self.solve_correctly_test(m, solve)
        with task_messenger(task, GridWorld) as m:
            self.timeout_test(m, solve)

"""
    # tasks testing routines
"""


def testAssociateObjectWithProperty(self):
    """ # this has been moved into repetition

    :return:
    """
    def solve(m):
        """ # find the answer in the instructions

        :param m:
        :return:
        """
        verb, = m.search_last_message(r"'I (\w+)'")
        m.send("I {verb}.".format(verb=verb))
    self.do_test_battery(repetition.VerbTask, solve)

    def testTurningTask(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            direction, = m.search_last_message(r"Turn (\w+)")
            m.send("I turn {direction}.".format(direction=direction))
        self.do_test_battery(navigation.TurningTask, solve)

    def testMoving(self):
        """ # find the answer in the instructions

        :param self:
        :return:
        """
        def solve(m):
            """

            :param m:
            :return:
            """
            m.send("I move forward.")
            self.do_test_battery(navigation.MovingTask, solve)

    def testMovingRelative(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """ # wait for feedback # move

            :param m:
            :return:
            """
            direction, = m.search_last_message(r"Move (\w+)")
            m.send("I turn {direction}.".format(direction=direction))
            m.read()
            m.send("I move forward.")
            self.do_test_battery(navigation.MovingRelativeTask, solve)

    def testMovingAbsolute(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """ # wait for feedback # move

            :param m:
            :return:
            """
            init_direction, dest_direction = m.search_last_message(r"facing (\w+), move (\w+)")
            directions = ['north', 'east', 'south', 'west']
            init_dir_idx = directions.index(init_direction)
            dest_dir_idx = directions.index(dest_direction)
            delta = (dest_dir_idx - init_dir_idx) % 4
            if delta == 3:
                delta = -1
            if delta > 0:
                direction = "right"
            else:
                direction = "left"
            for i in range(abs(delta)):
                m.send("I turn {direction}.".format(direction=direction))
                m.read()
            m.send("I move forward.")
        self.do_test_battery(navigation.MovingAbsoluteTask, solve)

    def testPickUp(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """

            :param m:
            :return:
            """
            object_, = m.search_last_message(r"Pick up the (\w+)")
            m.send("I pick up the {object}.".format(object=object_))
        self.do_test_battery(navigation.PickUpTask, solve)

    def testPickUpAround(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """ # wait for feedback # pick up the object

            :param m:
            :return:
            """
            dest_direction, object_ = m.search_last_message(r"(\w+) from you, pick up the (\w+)")
            directions = ['north', 'east', 'south', 'west']
            init_dir_idx = directions.index('north')
            dest_dir_idx = directions.index(dest_direction)
            delta = (dest_dir_idx - init_dir_idx) % 4
            if delta == 3:
                delta = -1
            if delta > 0:
                direction = "right"
            else:
                direction = "left"
            for i in range(abs(delta)):
                m.send("I turn {direction}.".format(direction=direction))
                m.read()
            m.send("I pick up the {object}.".format(object=object_))
        self.do_test_battery(navigation.PickUpAroundTask, solve)

    def testPickUpInFront(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """ # wait for feedback # move

            :param m:
            :return:
            """
            nsteps, object_ = m.search_last_message(r"(\w+) steps forward, pick up the (\w+)")
            nsteps = msg.string_to_number(nsteps)
            for i in range(nsteps - 1):
                m.send("I move forward.")
                m.read()
            m.send("I pick up the {object}.".format(object=object_))
        self.do_test_battery(navigation.PickUpInFrontTask, solve)

    def testGiving(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """

            :param m:
            :return:
            """
            article, object_ = m.search_last_message(r"I gave you (\w+) (\w+)")
            m.send("I give you {article} {object}.".format(article=article, object=object_))
        self.do_test_battery(navigation.GivingTask, solve)

    def testPickUpAroundAndGive(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """

            :param m:
            :return:
            """
            article, object_, dest_direction = m.search_last_message(r"There is (\w+) (\w+) (\w+)")
            directions = ['north', 'east', 'south', 'west']
            init_dir_idx = directions.index('north')
            dest_dir_idx = directions.index(dest_direction)
            delta = (dest_dir_idx - init_dir_idx) % 4
            if delta == 3:
                delta = -1
            if delta > 0:
                direction = "right"
            else:
                direction = "left"
            for i in range(abs(delta)):
                m.send("I turn {direction}.".format(direction=direction))
                # wait for feedback
                m.read()
            m.send("I pick up the {object}.".format(object=object_))
            m.read()
            m.send("I give you {article} {object}.".format(article=article, object=object_))
        self.do_test_battery(navigation.PickUpAroundAndGiveTask, solve)

    def testCountingInventoryGiving(self):
        """

        :param self:
        :return:
        """
        def solve(m):
            """ # I don't have anything in the beginning # The teacher just gave me somthing # Give the object back
            to the teacher # I don't have anything anymore

            :param m:
            :return:
            """
            object_, = m.search_last_message(r"How many (\w+)")
            m.send(msg.number_to_string(0) + ".")
            m.read()
            article, object_, = m.search_last_message(r"I gave you (\w+) (\w+)")
            m.send(msg.number_to_string(1) + ".")
            m.read()
            m.send("I give you {article} {object}.".format(article=article, object=object_))
            m.read()
            m.send(msg.number_to_string(0) + ".")
        self.do_test_battery(navigation.CountingInventoryGivingTask, solve)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
