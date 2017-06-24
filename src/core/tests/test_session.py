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
import core.task as task
import core.session as session
import core.serializer as serializer
import core.environment as environment
from core.obs.observer import Observable
from learners.base import BaseLearner


class NullTask(task.Task):
    """

    """
    def __init__(self):
        """

        """
        super(NullTask, self).__init__(max_time=100)


class EnvironmentMock(object):
    """

    """
    def __init__(self):
        """

        """
        self.task_updated = Observable()

    def set_task(self, task):
        """

        :param task:
        :return:
        """
        self.task = task

    def next(self, token):
        """

        :param token:
        :return:
        """
        self.task_updated(self.task)
        # always return a reward of 1
        return token, 1

    def raise_event(self, event):
        """

        :param event:
        :return:
        """
        pass

    def set_task_scheduler(self, ts):
        """

        :param ts:
        :return:
        """
        pass


class LearnerMock(object):
    def next(self, token):
        """

        :param token:
        :return:
        """
        return token

    def try_reward(self, r):
        """

        :param r:
        :return:
        """
        pass


class SingleTaskScheduler():
    def __init__(self, task):
        """

        :param task:
        """
        self.task = task

    def get_next_task(self):
        """

        :return:
        """
        return self.task

    def reward(self, reward):
        """

        :param reward:
        :return:
        """
        pass


class TestSession(unittest.TestCase):

    def testLimitReward(self):
        """

        :return:
        """
        env = environment.Environment(serializer.StandardSerializer(), SingleTaskScheduler(NullTask()), byte_mode=True)
        learner = LearnerMock()
        s = session.Session(env, learner)

        def on_time_updated(t):
            """

            :param t:
            :return:
            """
            if t >= 20:
                s.stop()
        s.total_time_updated.register(on_time_updated)

        s.run()
        self.assertLessEqual(s._total_reward, 10)

    def testAllInputs(self):
        """

        :return:
        """
        env = environment.Environment(serializer.StandardSerializer(), SingleTaskScheduler(NullTask()), byte_mode=True)
        learner = TryAllInputsLearner()
        s = session.Session(env, learner)

        def on_time_updated(t):
            if t >= 600:
                s.stop()
        s.total_time_updated.register(on_time_updated)
        s.run()


class TryAllInputsLearner(BaseLearner):
    """

    """
    char = -1

    def reward(self, reward):
        """

        :param reward:
        :return:
        """
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        """

        :param input:
        :return:
        """
        self.char += 1
        return chr(self.char % 256)

