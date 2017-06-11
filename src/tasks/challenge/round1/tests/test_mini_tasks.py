# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import re
import unittest

import core.environment as environment
import core.serializer as serializer
import tasks.challenge.round1.challenge_mini as comm_ai_mini
from core.scheduler import ConsecutiveTaskScheduler
from learners.base import BaseLearner
from tasks.challenge.round1.tests.test_micro_tasks import EnvironmentByteMessenger, FixedLearner
from tasks.competition.tests.helpers import SingleTaskScheduler
from tasks.competition.tests.helpers import task_messenger as commai_messenger
from worlds.grid_world import GridWorld


class TestCommAIMiniBase(unittest.TestCase):
    """

    """

    @classmethod
    def setUpClass(cls):
        """

        :return:
        """
        if cls is TestCommAIMiniBase:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")
        super(TestCommAIMiniBase, cls).setUpClass()

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(TestCommAIMiniBase, self).__init__(*args, **kwargs)
        self.task_set = None

    def _obtains_feedback(self, m):
        """

        :param m:
        :return:
        """
        feedback_len = m.read()
        self.assertGreater(feedback_len, 0)

    def test_new_correct(self):
        """

        :return:
        """
        with commai_messenger(self.task_set, GridWorld) as m:
            m.read()
            correct_answer = m._env._task_scheduler.task.answer + '.'
            m.send(correct_answer)
            self._obtains_feedback(m)
            m.send()
            self.assertEqual(m.get_cumulative_reward(), 1)

    def test_new_timeout(self):
        """

        :return:
        """
        with commai_messenger(self.task_set, GridWorld) as m:
            m.read()
            while m.is_silent():
                m.send()
            self._obtains_feedback(m)
            feedback = m.get_last_message()
            self.assertTrue('Wrong' in feedback)
            m.send()
            self.assertEqual(m.get_cumulative_reward(), 0)

    def test_error_answer(self):
        """

        :return:
        """
        with commai_messenger(self.task_set, GridWorld) as m:
            m.read()
            m.send("wrong answer.")

            self._obtains_feedback(m)
            feedback = m.get_last_message()
            self.assertTrue('Wrong' in feedback)

            m.send()
            self.assertEqual(m.get_cumulative_reward(), 0)


class TestCommAIMiniTS1(TestCommAIMiniBase):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(TestCommAIMiniTS1, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet1


class TestCommAIMiniTS2(TestCommAIMiniBase):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(TestCommAIMiniTS2, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet2


class TestCommAIMiniTS3(TestCommAIMiniBase):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(TestCommAIMiniTS3, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet3


class TestCommAIMiniTS4(TestCommAIMiniBase):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(TestCommAIMiniTS4, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet4


class TestCommAIMiniTS5(TestCommAIMiniBase):
    """

    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(TestCommAIMiniTS5, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet5


def task_solved_successfuly(task):
    """

    :param task:
    :return:
    """
    return task._env._last_result


def basic_task_run(test, messenger, learner, task):
    """# raise the timeout constant on these tasks, because they are not finishing. on nr_of_questions timeout, but
    on nr_of_characters timeout  # agent succeeded

    :param test:
    :param messenger:
    :param learner:
    :param task:
    :return:
    """
    limit = task._max_time
    while True:
        limit -= 1
        if limit < 1:
            test.assertFalse(True)
            break
        question = messenger.get_text()[-1]
        answer = learner.next(question)
        reward = messenger.send(answer)
        learner.reward(reward)
        if task._env._last_result is not None:
            break


def task_messenger(task):
    """

    :param task:
    :return:
    """
    slzr = serializer.StandardSerializer()
    scheduler = SingleTaskScheduler(task)
    env = environment.Environment(slzr, scheduler, max_reward_per_task=float("inf"), byte_mode=True)
    return EnvironmentByteMessenger(env, slzr)


class TestMicroTaskBase(unittest.TestCase):
    """

    """
    task = None
    task_instance_multiplier = 3
    task_run_multiplier = 10

    @classmethod
    def setUpClass(cls):
        """

        :return:
        """
        if cls is TestMicroTaskBase:
            raise unittest.SkipTest("Skip MicroTaskBase tests, it's a base class")
        super(TestMicroTaskBase, cls).setUpClass()

    def _get_task(self):
        """

        :return:
        """
        task = self.task()
        task.success_tolerance = 0
        task.failed_task_tolerance = 0
        return task

    def _get_learner(self):
        """

        :return:
        """
        pass

    def _get_failing_learner(self):
        """

        :return:
        """
        return FixedLearner('*')

    def init_env(self, task, success_threshold=2):
        """

        :param task:
        :param success_threshold:
        :return:
        """
        slzr = serializer.StandardSerializer()
        scheduler = ConsecutiveTaskScheduler([task], success_threshold)
        env = environment.Environment(slzr, scheduler, max_reward_per_task=float("inf"), byte_mode=True)
        messenger = EnvironmentByteMessenger(env, slzr)
        return (scheduler, messenger)

    def test_task(self):
        """

        :return:
        """
        for _ in range(self.task_instance_multiplier):
            task = self._get_task()
            for _ in range(self.task_run_multiplier):
                learner = self._get_learner()
                messenger = task_messenger(task)
                basic_task_run(self, messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_successful_evaluation(self):
        """# Tests that task instance can be solved and that there are no residuals from 1st instance, which would
         prevent agent from solving 2nd instance# first run# second run # 2 % 2 = 0, because the scheduler switched
         to next task

        :return:
        """
        task = self._get_task()
        scheduler, messenger = self.init_env(task)
        learner = self._get_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertTrue(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 1)
        learner = self._get_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertTrue(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 0)

    def test_failed_evaluation(self):
        """# Tests that instance can be failed and that there are no residuals from 1st instance, which would solve
        the 2nd instance instead of agent # first run # second run

        :return:
        """
        task = self.task()
        scheduler, messenger = self.init_env(task)
        learner = self._get_failing_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertFalse(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 0)
        basic_task_run(self, messenger, learner, task)
        self.assertFalse(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 0)


class TestCommAIMiniNewTS1(TestMicroTaskBase):
    """

    """
    task = comm_ai_mini.TaskSet1

    def _get_learner(self):
        """

        :return:
        """
        return Mini1Learner()

    def _get_failing_learner(self):
        """

        :return:
        """
        return FixedLearner('.')


class TestMatchQuestionAndFeedbackBase(BaseLearner):
    """

    """
    matcher_feedback = None
    matcher_output = None

    def __init__(self):
        """

        """
        self._buffer = []
        self._read_assignment = True
        self._output = []

    def next(self, input_char):
        """ # Commands received. # Get the whole assignment, remove dot.

        :param input_char:
        :return:
        """
        self._buffer.append(input_char)
        if self._read_assignment:
            if input_char == '.':
                received_sentence = ''.join(self._buffer)
                if self.matcher_feedback is None:
                    feedback_match = ['']
                else:
                    feedback_match = self.matcher_feedback.findall(received_sentence)
                output_match = self.matcher_output.findall(received_sentence)
                if len(output_match) > 0:
                    self._output = list(self.generate_response(feedback_match, output_match))
                    self._buffer = []
                    self._read_assignment = False
        if not self._read_assignment:
            if len(self._output) > 0:
                return self._output.pop(0)
            else:
                self._read_assignment = True
                return '.'
        return ' '

    def generate_response(self, feedback_match, output_match):
        """

        :param feedback_match:
        :param output_match:
        :return:
        """
        raise NotImplementedError()


def verify_description(verify, description):
    """

    :param verify:
    :param description:
    :return:
    """
    verification_array = [False for _ in verify]
    window_length = len(description)
    for i in range(0, len(verify) - window_length + 1):
        covers = description == verify[i:i + window_length]
        verification_array[i:i + window_length] = [covers or verification_array[i + j] for j in range(0, window_length)]
    return all(verification_array)


class Mini1Learner(TestMatchQuestionAndFeedbackBase):
    """

    """
    matcher_output = re.compile('description: (.+); verify: (.+)\.')

    def generate_response(self, feedback_match, output_match):
        """

        :param feedback_match:
        :param output_match:
        :return:
        """
        description = output_match[0][0]
        verify = output_match[0][1]
        if verify_description(verify, description):
            return 'true'
        else:
            return 'false'
