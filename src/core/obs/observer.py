# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.


class Observable(object):
    """
    Simple implementation of the observer pattern
    """
    def __init__(self):
        """

        """
        self.observers = []

    def register(self, callback):
        """

        :param callback:
        :return:
        """
        self.observers.append(callback)

    def deregister(self, callback):
        """

        :param callback:
        :return:
        """
        self.observers.remove(callback)

    def __call__(self, *args):
        """

        :param args:
        :return:
        """
        for c in self.observers:
            c(*args)
