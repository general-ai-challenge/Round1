# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import zmq
import signal

port = 5556
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect("tcp://172.18.0.1:%s" % port)
socket.send_string("hello")


def handler(signal, frame):
    """

    :param signal:
    :param frame:
    :return:
    """
    print('exiting...')
    socket.disconnect("tcp://172.18.0.1:%s" % port)
    exit()

signal.signal(signal.SIGINT, handler)

reward = socket.recv()
next_input = socket.recv()

while True:
    socket.send_string("a")  # your attempt to solve the current task
    reward = socket.recv()
    next_input = socket.recv()
    print(reward)

signal.pause()
