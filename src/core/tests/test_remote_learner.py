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
import random


def main():
    """# think...

    :return:
    """
    port = "5556"
    context = zmq.Context()
    socket = context.socket(zmq.PAIR)
    socket.connect("tcp://localhost:%s" % port)
    socket.send_string(str('hello'))

    message = '00101110'
    cnt = 0
    while True:
        reward = socket.recv()  # 1 or 0, or '-1' for None
        print(reward)
        msg_in = socket.recv()
        print(msg_in)
        msg_out = str(random.getrandbits(1) if cnt % 7 == 0 else 1)
        if cnt % 2 == 0:
            msg_out = str(message[cnt % 8])
        socket.send(msg_out)
        cnt = cnt + 1

if __name__ == '__main__':
    main()
