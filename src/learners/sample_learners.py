# -*- coding: utf-8
# 'version': '0.3'
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

# TODO fix imports
from core.serializer import StandardSerializer, IdentitySerializer
from learners.base import BaseLearner


class SampleRepeatingLearner(BaseLearner):
    """

    """
    def reward(self, reward):
        """ # YEAH! Reward!!! Whatever...

        :param reward:
        :return:
        """
        pass

    def next(self, input):
        # TODO input shadow
        """# do super fancy computations return our guess

        :param input:
        :return:
        """
        return input


class SampleSilentLearner(BaseLearner):
    def __init__(self):
        """

        """
        self.serializer = StandardSerializer()
        self.silence_code = self.serializer.to_binary(' ')
        self.silence_i = 0

    def reward(self, reward):
        # TODO reward not used
        """ YEAH! Reward!!! Whatever...

        :param reward:
        :return:
        """
        self.silence_i = 0

    def next(self, input):
        # TODO input shadow not used
        """

        :param input:
        :return:
        """
        output = self.silence_code[self.silence_i]
        self.silence_i = (self.silence_i + 1) % len(self.silence_code)
        return output


class SampleMemorizingLearner(BaseLearner):
    """

    """
    def __init__(self):
        """ the learner has the serialization hardcoded to detect spaces

        """
        self.memory = ''
        self.teacher_stopped_talking = False

        self.serializer = StandardSerializer()
        self.silence_code = self.serializer.to_binary(' ')
        self.silence_i = 0

    def reward(self, reward):
        # TODO reward not used
        """# YEAH! Reward!!! Whatever... Now this robotic teacher is going to mumble things again

        :param reward:
        :return:
        """
        self.teacher_stopped_talking = False
        self.silence_i = 0
        self.memory = ''

    def next(self, input):
        # TODO input shadow
        """# If we have received a silence byte  # send the memorized sequence # memorize what the teacher said

        :param input:
        :return:
        """
        text_input = self.serializer.to_text(self.memory)
        if text_input and text_input[-2:] == '  ':
            self.teacher_stopped_talking = True
        if self.teacher_stopped_talking:
            output, self.memory = self.memory[0], self.memory[1:]
        else:
            output = self.silence_code[self.silence_i]
            self.silence_i = (self.silence_i + 1) % len(self.silence_code)
        self.memory += input
        return output
