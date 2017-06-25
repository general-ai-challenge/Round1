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

import platform
if platform.python_version_tuple()[0] == '2':
    from kitchen.text.converters import to_unicode


class ByteInputChannel:
    """

    """
    def __init__(self, serializer):
        """ remembers the input in binary format.  leftmost deserialization of the binary buffer.  remember the
        position until which we deserialized the binary buffer

        :param serializer:
        """
        self.serializer = serializer
        self._buffer = u''
        self.message_updated = Observable()
        self.sequence_updated = Observable()

    def consume(self, input_char):
        """Takes a byte into the channel

        :param input_char:
        :return:
        """
        if ord(input_char) >= 256:
            raise Exception("Input char out of range")
        if platform.python_version_tuple()[0] == '2':
            encoded_char = to_unicode(input_char, 'utf-8')
        else:
            encoded_char = input_char
        self._buffer += encoded_char
        self.message_updated(self._buffer)
        self.sequence_updated(self._buffer)

    def clear(self):
        """Clears all the  buffers

        :return:
        """
        self._set_buffer(u'')

    def _set_buffer(self, new_buffer):
        """Replaces the deserialized part of the buffer.

        :param new_buffer:
        :return:
        """
        if self._buffer != new_buffer:
            self._buffer = new_buffer
            self.message_updated(self._buffer)
            self.sequence_updated(self._buffer)

    def get_text(self):
        """

        :return:
        """
        return self._buffer

    def get_undeserialized(self):
        # TODO static
        """ Returns the yet non deserialized chunk in the input

        :return:
        """
        return u''

    def set_deserialized_buffer(self, new_buffer):
        """ Replaces the deserialized part of the buffer.

        :param new_buffer:
        :return:
        """
        self._buffer = new_buffer


class ByteOutputChannel:
    """

    """

    def __init__(self, serializer):
        """ remembers the data that has to be shipped out.  event that gets fired every time we change the output
        sequence

        :param serializer:
        """
        self.serializer = serializer
        self._buffer = u''
        self.sequence_updated = Observable()
        self.logger = logging.getLogger(__name__)

    def set_message(self, message):
        """

        :param message:
        :return:
        """
        self._buffer += message
        self.sequence_updated(self._buffer)

    def clear(self):
        """

        :return:
        """
        self._set_buffer(u'')

    def _set_buffer(self, new_buffer):
        """ Carefully raise the event only if the buffer has actually changed

        :param new_buffer:
        :return:
        """
        if self._buffer != new_buffer:
            self._buffer = new_buffer
            self.sequence_updated(self._buffer)

    def consume(self):
        """

        :return:
        """
        if len(self._buffer) > 0:
            output, new_buffer = self._buffer[0], self._buffer[1:]
            self._set_buffer(new_buffer)
            return output

    def is_empty(self):
        """

        :return:
        """
        return len(self._buffer) == 0

    def is_silent(self):
        """ All the bytes in the output are silent tokens. '

        :return:
        """
        return self._buffer.strip(self.serializer.SILENCE_TOKEN) == u''
