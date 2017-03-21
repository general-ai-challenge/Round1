# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from core.obs.observer import Observable
import logging

import platform
if platform.python_version_tuple()[0] == '2':
    from kitchen.text.converters import to_unicode


class ByteInputChannel:

    def __init__(self, serializer):
        self.serializer = serializer
        # remembers the input in binary format
        # leftmost deserialization of the binary buffer
        self._buffer = u''
        # remember the position until which we deserialized the binary buffer

        self.message_updated = Observable()
        self.sequence_updated = Observable()

    def consume(self, input_char):
        '''
        Takes a byte into the channel
        '''
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
        '''Clears all the  buffers'''
        self._set_buffer(u'')

    def _set_buffer(self, new_buffer):
        '''
        Replaces the deserialized part of the buffer.
        '''
        if self._buffer != new_buffer:
            self._buffer = new_buffer
            self.message_updated(self._buffer)
            self.sequence_updated(self._buffer)

    def get_text(self):
        return self._buffer

    def get_undeserialized(self):
        '''
        Returns the yet non deserialized chunk in the input
        '''
        return u''

    def set_deserialized_buffer(self, new_buffer):
        '''
        Replaces the deserialized part of the buffer.
        '''
        self._buffer = new_buffer


class ByteOutputChannel:

    def __init__(self, serializer):
        self.serializer = serializer
        self._buffer = u''
        # remembers the data that has to be shipped out
        # event that gets fired every time we change the output sequence
        self.sequence_updated = Observable()
        self.logger = logging.getLogger(__name__)

    def set_message(self, message):
        self._buffer += message
        self.sequence_updated(self._buffer)

    def clear(self):
        self._set_buffer(u'')

    def _set_buffer(self, new_buffer):
        '''
        Carefully raise the event only if the buffer has actually changed
        '''
        if self._buffer != new_buffer:
            self._buffer = new_buffer
            self.sequence_updated(self._buffer)

    def consume(self):
        if len(self._buffer) > 0:
            output, new_buffer = self._buffer[0], \
                self._buffer[1:]
            self._set_buffer(new_buffer)
            return output

    def is_empty(self):
        return len(self._buffer) == 0

    def is_silent(self):
        ''' All the bytes in the output are silent tokens. '''
        return self._buffer.strip(self.serializer.SILENCE_TOKEN) == u''
