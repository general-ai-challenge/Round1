# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.


class Observable(object):
    '''Simple implementation of the observer pattern'''

    def __init__(self):
        self.observers = []

    def register(self, callback):
        self.observers.append(callback)

    def deregister(self, callback):
        self.observers.remove(callback)

    def __call__(self, *args):
        for c in self.observers:
            c(*args)
