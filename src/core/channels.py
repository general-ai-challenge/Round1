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
from core.obs.observer import Observable
import logging


class InputChannel:

    def __init__(self, serializer):
        """ remembers the input in binary format.  leftmost deserialization of the binary buffer.  remember the
        position until which we deserialized the binary buffer.  event that gets fired for every new bit.  event
        that gets fired for every new character

        :param serializer:
        """
        self.serializer = serializer
        self._binary_buffer = ''
        self._deserialized_buffer = ''
        self._deserialized_pos = 0
        self.sequence_updated = Observable()
        self.message_updated = Observable()

    def consume(self, input_bit):
        """  Takes a bit into the channel.  for now we are storing the input as strings (let's change this later).
        store the bit in the binary input buffer.  notify the updated sequence.  we check if we can deserialize the
        final part of the sequence.  when we do, we deserialize the chunk.  we update the position

        :param input_bit:
        :return:
        """
        if input_bit == 0 or input_bit == 1:
            input_bit = str(input_bit)
        self._binary_buffer += input_bit
        self.sequence_updated(self._binary_buffer)
        undeserialized_part = self.get_undeserialized()
        if self.serializer.can_deserialize(undeserialized_part):
            self._deserialized_buffer += self.serializer.to_text(undeserialized_part)
            self._deserialized_pos += len(undeserialized_part)
            self.message_updated(self._deserialized_buffer)

    def clear(self):
        """ Clears all the  buffers

        :return:
        """
        self._set_deserialized_buffer('')
        self._set_binary_buffer('')
        self._deserialized_pos = 0

    def get_binary(self):
        """

        :return:
        """
        return self._binary_buffer

    def set_deserialized_buffer(self, new_buffer):
        """ Replaces the deserialized part of the buffer.

        :param new_buffer:
        :return:
        """
        self._deserialized_buffer = new_buffer

    def get_undeserialized(self):
        """ Returns the yet non deserialized chunk in the input

        :return:
        """
        return self._binary_buffer[self._deserialized_pos:]

    def get_text(self):
        """

        :return:
        """
        return self._deserialized_buffer

    def _set_binary_buffer(self, new_buffer):
        """  Carefully raise the event only if the buffer has actually changed

        :param new_buffer:
        :return:
        """
        if self._binary_buffer != new_buffer:
            self._binary_buffer = new_buffer
            self.sequence_updated(self._binary_buffer)

    def _set_deserialized_buffer(self, new_buffer):
        """ Carefully raise the event only if the buffer has actually changed

        :param new_buffer:
        :return:
        """
        if self._deserialized_buffer != new_buffer:
            self._deserialized_buffer = new_buffer
            self.message_updated(self._deserialized_buffer)


class OutputChannel:
    """

    """

    def __init__(self, serializer):
        """ remembers the data that has to be shipped out.  event that gets fired every time we change the output sequence

        :param serializer:
        """
        self.serializer = serializer
        self._binary_buffer = ''
        self.sequence_updated = Observable()
        self.logger = logging.getLogger(__name__)

    def set_message(self, message):
        """ find the first available point from where we can insert.  the new buffer without breaking the encoding.
        if we can decode from insert_point on, we can replace.  that information with the new buffer

        :param message:
        :return:
        """
        new_binary = self.serializer.to_binary(message)
        insert_point = len(self._binary_buffer)
        for i in range(len(self._binary_buffer)):
            if self.serializer.to_text(self._binary_buffer[i:]):
                insert_point = i
                break
        if insert_point > 0:
            self.logger.debug("Inserting new contents at {0}".format(insert_point))
        self._set_buffer(self._binary_buffer[:insert_point] + new_binary)

    def clear(self):
        """

        :return:
        """
        self._set_buffer('')

    def _set_buffer(self, new_buffer):
        """ Carefully raise the event only if the buffer has actually changed

        :param new_buffer:
        :return:
        """
        if self._binary_buffer != new_buffer:
            self._binary_buffer = new_buffer
            self.sequence_updated(self._binary_buffer)

    def consume(self):
        """

        :return:
        """
        if len(self._binary_buffer) > 0:
            output, new_buffer = self._binary_buffer[0], self._binary_buffer[1:]
            self._set_buffer(new_buffer)
            return output

    def is_empty(self):
        """

        :return:
        """
        return len(self._binary_buffer) == 0

    def is_silent(self):
        """ All the bits in the output token are the result of serializing
        silence tokens

        :return:
        """
        buf = self._binary_buffer
        silent_bits = self.serializer.to_binary(self.serializer.SILENCE_TOKEN)
        token_size = len(silent_bits)
        while len(buf) > token_size:
            buf_suffix, buf = buf[-token_size:], buf[:-token_size]
            if buf_suffix != silent_bits:
                return False
        return len(buf) == 0 or buf == silent_bits[-len(buf):]
