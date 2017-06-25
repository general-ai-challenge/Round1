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
from core.byte_channels import ByteInputChannel, ByteOutputChannel
from core.channels import InputChannel, OutputChannel
from learners.base import BaseLearner
import logging
import re


class HumanLearner(BaseLearner):
    """

    """
    def __init__(self, serializer, byte_mode):
        """Takes the serialization protocol

        :param serializer:
        :param byte_mode:
        """
        self._serializer = serializer
        if byte_mode:
            self._input_channel = ByteInputChannel(serializer)
            self._output_channel = ByteOutputChannel(serializer)
        else:
            self._input_channel = InputChannel(serializer)
            self._output_channel = OutputChannel(serializer)
        self._input_channel.message_updated.register(self.on_message)
        self.logger = logging.getLogger(__name__)
        self.speaking = False

    def set_view(self, view):
        """ Sets the user interface to get the user input

        :param view:
        :return:
        """
        self._view = view

    def reward(self, reward):
        """

        :param reward:
        :return:
        """
        self.logger.info("Reward received: {0}".format(reward))
        self._input_channel.clear()
        self._output_channel.clear()

    def next(self, input):
        # TODO input shadow
        """ If the buffer is empty, fill it with silence # Add one silence token to the buffer # Get the bit to return
        Interpret the bit from the learner

        :param input:
        :return:
        """
        if self._output_channel.is_empty():
            self.logger.debug("Output buffer is empty, filling with silence")
            self._output_channel.set_message(self._serializer.SILENCE_TOKEN)
        output = self._output_channel.consume()
        self._input_channel.consume(input)
        return output

    def on_message(self, message):
        """ we ask for input on two consecutive silences # If we were speaking, we are not speaking anymore

        :param message:
        :return:
        """
        if message[-2:] == self._serializer.SILENCE_TOKEN * 2 and \
                self._output_channel.is_empty() and not self.speaking:
            self.ask_for_input()
        elif self._output_channel.is_empty():
            self.speaking = False

    def ask_for_input(self):
        """

        :return:
        """
        output = self._view.get_input()
        self.logger.debug(u"Received input from the human: '{0}'".format(output))
        if output:
            self.speaking = True
            output = re.compile('\.+').sub('.', output)
            self._output_channel.set_message(output)


class ImmediateHumanLearner(HumanLearner):
    """

    """
    def __init__(self, serializer, byte_mode):
        """ Takes the serialization protocol

        :param serializer:
        :param byte_mode:
        """
        self._serializer = serializer
        if byte_mode:
            self._input_channel = ByteInputChannel(serializer)
            self._output_channel = ByteOutputChannel(serializer)
        else:
            self._input_channel = InputChannel(serializer)
            self._output_channel = OutputChannel(serializer)
        self.logger = logging.getLogger(__name__)
        self.speaking = False

    def on_message(self, message):
        """ # Ask for input # If the buffer is empty, fill it with silence # Add one silence token to the buffer Get
        the bit to return # Interpret the bit from the learner

        :param message:
        :return:
        """
        self.ask_for_input()

    def next(self, input):
        # TODO input shadow
        """

        :param input:
        :return:
        """
        self.ask_for_input()
        if self._output_channel.is_empty():
            self.logger.debug("Output buffer is empty, filling with silence")
            self._output_channel.set_message(self._serializer.SILENCE_TOKEN)
        output = self._output_channel.consume()
        self._input_channel.consume(input)
        return output


class HaltOnDotHumanLearner(HumanLearner):
    """

    """
    def __init__(self, serializer, byte_mode):
        """

        :param serializer:
        :param byte_mode:
        """
        super(HaltOnDotHumanLearner, self).__init__(serializer, byte_mode)

    def on_message(self, message):
        """# we ask for input on two consecutive silences If we were speaking, we are not speaking anymore

        :param message:
        :return:
        """
        if message[-1:] == '.' and self._output_channel.is_empty() and not self.speaking:
            self.ask_for_input()
        elif self._output_channel.is_empty():
            self.speaking = False
