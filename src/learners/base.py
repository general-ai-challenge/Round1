# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

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

    def __init__(self, cmd, port):
        try:
            import zmq
        except ImportError:
            raise ImportError("Must have zeromq for remote learner.")

        self.port = port if port is not None else 5556
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % port)

        # launch learner
        if cmd is not None:
            subprocess.Popen((cmd + ' ' + str(self.port)).split())
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
