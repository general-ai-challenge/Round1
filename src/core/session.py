# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.
from core.obs.observer import Observable
from collections import defaultdict
import time

class Session:
    """

    """
    def __init__(self, environment, learner, default_sleep=0.01):
        """# internal initialization# listen to changes in the currently running task# observable status.
         -- accounting -- total time# total cumulative reward# keep track of how many times we have tried each task
        # keep track of how much time we have spent on each task

        :param environment:
        :param learner:
        :param default_sleep:
        """
        self._env = environment
        self._learner = learner
        self._default_sleep = default_sleep
        self._sleep = self._default_sleep
        self._env.task_updated.register(self.on_task_updated)
        self.env_token_updated = Observable()
        self.learner_token_updated = Observable()
        self.total_reward_updated = Observable()
        self.total_time_updated = Observable()
        self._total_time = 0
        self._total_reward = 0
        self._task_count = defaultdict(int)
        self._task_time = defaultdict(int)

    def run(self):
        """# initialize a token variable# send out initial values of status variables# loop until stopped# first
        speaks the environment one token (one bit)# reward the learner if it has been set# allow some time before
        processing the next iteration# then speaks the learner one token# and we loop

        :return:
        """
        token = None
        self.total_time_updated(self._total_time)
        self.total_reward_updated(self._total_reward)
        self._stop = False
        while not self._stop:
            token, reward = self._env.next(token)
            self.env_token_updated(token)
            self._learner.try_reward(reward)
            self.accumulate_reward(reward)
            if self._sleep > 0:
                time.sleep(self._sleep)
            token = self._learner.next(token)
            self.learner_token_updated(token)
            self._total_time += 1
            self._task_time[self._current_task.get_name()] += 1
            self.total_time_updated(self._total_time)

    def stop(self):
        """

        :return:
        """
        self._stop = True

    def get_total_time(self):
        """

        :return:
        """
        return self._total_time

    def get_total_reward(self):
        """

        :return:
        """
        return self._total_reward

    def get_reward_per_task(self):
        """

        :return:
        """
        return self._env.get_reward_per_task()

    def get_task_count(self):
        """

        :return:
        """
        return self._task_count

    def get_task_time(self):
        """

        :return:
        """
        return self._task_time

    def accumulate_reward(self, reward):
        """Records the reward if the learner hasn't exceeded the maximum possible amount of reward allowed for the
        current task.

        :param reward:
        :return:
        """
        if reward is not None:
            self._total_reward += reward
            if reward != 0:
                self.total_reward_updated(self._total_reward)

    def on_task_updated(self, task):
        """

        :param task:
        :return:
        """
        self._current_task = task
        self._task_count[self._current_task.get_name()] += 1

    def set_sleep(self, sleep):
        """

        :param sleep:
        :return:
        """
        if sleep < 0:
            sleep = 0
        self._sleep = sleep

    def get_sleep(self):
        """

        :return:
        """
        return self._sleep

    def add_sleep(self, dsleep):
        """

        :param dsleep:
        :return:
        """
        self.set_sleep(self.get_sleep() + dsleep)

    def reset_sleep(self):
        """

        :return:
        """
        self._sleep = self._default_sleep
