# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import unittest
import core.task as task
import core.session as session
import core.serializer as serializer
import core.environment as environment
from core.obs.observer import Observable
from learners.base import BaseLearner


class NullTask(task.Task):
    def __init__(self):
        super(NullTask, self).__init__(max_time=100)


class EnvironmentMock(object):
    def __init__(self):
        self.task_updated = Observable()

    def set_task(self, task):
        self.task = task

    def next(self, token):
        self.task_updated(self.task)
        # always return a reward of 1
        return token, 1

    def raise_event(self, event):
        pass

    def set_task_scheduler(self, ts):
        pass


class LearnerMock(object):
    def next(self, token):
        return token

    def try_reward(self, r):
        pass


class SingleTaskScheduler():
    def __init__(self, task):
        self.task = task

    def get_next_task(self):
        return self.task

    def reward(self, reward):
        pass


class TestSession(unittest.TestCase):

    def testLimitReward(self):
        env = environment.Environment(serializer.StandardSerializer(), SingleTaskScheduler(NullTask()), byte_mode=True)
        learner = LearnerMock()
        s = session.Session(env, learner)

        def on_time_updated(t):
            if t >= 20:
                s.stop()
        s.total_time_updated.register(on_time_updated)

        s.run()
        self.assertLessEqual(s._total_reward, 10)

    def testAllInputs(self):
        env = environment.Environment(serializer.StandardSerializer(), SingleTaskScheduler(NullTask()), byte_mode=True)
        learner = TryAllInputsLearner()
        s = session.Session(env, learner)

        def on_time_updated(t):
            if t >= 600:
                s.stop()

        s.total_time_updated.register(on_time_updated)

        s.run()


class TryAllInputsLearner(BaseLearner):
    char = -1

    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        self.char += 1
        return chr(self.char % 256)

