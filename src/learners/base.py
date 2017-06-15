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
import subprocess


class BaseLearner(object):
    def try_reward(self, reward):
        if reward is not None:
            self.reward(reward)

    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        # do super fancy computations
        # return our guess
        return input


class RemoteLearner(BaseLearner):
    def __init__(self, cmd, port, address=None):
        try:
            import zmq
        except ImportError:
            raise ImportError("Must have zeromq for remote learner.")

        if address is None:
            address = '*'

        if port is None:
            port = 5556
        elif int(port) < 1 or int(port) > 65535:
            raise ValueError("Invalid port number: %s" % port)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://%s:%s" % (address, port))

        # launch learner
        if cmd is not None:
            subprocess.Popen((cmd + ' ' + str(port)).split())
        handshake_in = self.socket.recv().decode('utf-8')
        assert handshake_in == 'hello'  # handshake

    # send to learner, and get response;
    def next(self, inp):
        self.socket.send_string(str(inp))
        reply = self.receive_socket()
        return reply

    def try_reward(self, reward):
        reward = reward if reward is not None else 0
        self.socket.send_string(str(reward))

    def receive_socket(self):
        reply = self.socket.recv()
        if type(reply) == type(b''):
            reply = reply.decode('utf-8')
        return reply

    def set_view(self, view):
        pass


class RemoteTimedLearner(BaseLearner):
    def __init__(self, cmd, port, address=None):
        super().__init__(cmd, port, address)
