# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import core.environment as environment
import core.serializer as serializer
import core.channels as channels
import contextlib
import re


class EnvironmentMessenger:
    """

    """
    def __init__(self, env, serializer):
        """

        :param env:
        :param serializer:
        """
        self._env = env
        self._serializer = serializer
        self._input_channel = channels.InputChannel(serializer)
        self._output_channel = channels.OutputChannel(serializer)
        self.cum_reward = 0
        self.init()

    def init(self):
        """Kick-starts the environment

        :return:
        """
        first_symbol, reward = self._env.next(None)
        self._input_channel.consume(first_symbol)

    def is_silent(self):
        """

        :return:
        """
        return self._env._output_channel.is_silent()

    def read(self):
        """Sends silence until the teacher has stopped speaking # Keep on putting silence in the output channel

        :return:
        """
        nsymbols = 0
        while not self.is_silent():
            nsymbols += self.send(self._serializer.SILENCE_TOKEN)
        return nsymbols

    def read_until(self, condition):
        """Sends silence until a given condition holds true. # wrap the condition to catch exceptions
        Args:
            condition: a function that takes an EnvironmentMessenger
        """

        def safe_condition_eval():
            """  # Keep on putting silence in the output channel

            :return:
            """
            try:
                return condition(self)
            except BaseException:
                return False
        nsymbols = 0
        while not self.is_silent() and not safe_condition_eval():
            nsymbols += self.send(self._serializer.SILENCE_TOKEN)
        return nsymbols

    def send(self, msg=None):
        """# default message is a silence # puts the message in the output channel # send every symbol in it
        # send/receive a symbol and reward # save the symbol # save the reward # a reward marks the end of a task
        for now, so clear the buffers

        :param msg:
        :return:
        """

        if msg is None:
            msg = self._serializer.SILENCE_TOKEN
        nsymbols = 0
        self._output_channel.set_message(msg)
        while not self._output_channel.is_empty():
            env_symbol, reward = self._env.next(self._output_channel.consume())
            self._input_channel.consume(env_symbol)
            if reward is not None:
                self.cum_reward += reward
            nsymbols += 1
        return nsymbols

    def get_text(self):
        """

        :return:
        """
        return self._input_channel.get_text()

    def get_last_message(self, n_silence=2):
        """ Returns the last message sent by the teacher. The message is delimited between the end of the input
        stream and the point after n_silence silent tokens where issued. # get the input text  # remove the trailing
        silences # find the point where the last message started# (after at least n_silence tokens)

        :param n_silence:
        :return:
        """
        input_text = self._input_channel.get_text()
        input_text = input_text.rstrip(self._serializer.SILENCE_TOKEN)
        last_silence = input_text.rfind(self._serializer.SILENCE_TOKEN * n_silence)
        if last_silence == -1:
            return input_text
        else:
            return input_text[last_silence + n_silence:]

    def search_last_message(self, pattern):
        """

        :param pattern:
        :return:
        """
        message = self.get_last_message()
        match = re.search(pattern, message)
        if match is None:
            raise RuntimeError("'{0}' did not find any match on '{1}'".format(
                pattern, message
            ))
        return match.groups()

    def get_cumulative_reward(self):
        """

        :return:
        """
        return self.cum_reward

    def get_time(self):
        """

        :return:
        """
        return self._env._task_time


class SingleTaskScheduler():
    """

    """
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


@contextlib.contextmanager
def task_messenger(task_funct, world_funct=None):
    """ Returns an EnvironmentMessenger to interact with the created task.
    :param task_funct: takes an environment (optionally a world) and returns a task object.
    :param world_funct:  takes an environment and returns a world object.
    :return:
    """
    slzr = serializer.StandardSerializer()
    if world_funct:
        world = world_funct()
        task = task_funct(world)
    else:
        task = task_funct()
    scheduler = SingleTaskScheduler(task)
    env = environment.Environment(slzr, scheduler)
    m = EnvironmentMessenger(env, slzr)
    yield m
