# -*- coding: utf-8
# 'version': '0.2'
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import unittest
import core.events as events


class MyEvent(object):
    """

    """
    pass


class TestEvents(unittest.TestCase):
    """

    """
    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(TestEvents, self).__init__(*args, **kwargs)

    def testEvents(self):
        """

        :return:
        """
        self.event_raised = False

        def on_start(self, event):
            """

            :param self:
            :param event:
            :return:
            """
            self.event_raised = True

        em = events.EventManager()
        em.register(self,
                    events.Trigger(MyEvent, lambda e: True, on_start))
        em.raise_event(MyEvent())
        self.assertTrue(self.event_raised)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
