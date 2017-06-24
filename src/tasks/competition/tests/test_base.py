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
# TODO grid_world, competition.tests.helpers unresolved ref
import unittest
import tasks.competition.base as base
from core.task import on_start, on_message
from tasks.competition.tests.helpers import task_messenger


class TestBase(unittest.TestCase):
    """

    """
    def testIgnoreInterruptions(self):
        """

        :return:
        """
        class TestTask(base.BaseTask):
            """

            """
            def __init__(self, max_time=1000):
                """

                :param max_time:
                """
                super(TestTask, self).__init__(max_time=max_time)

            @on_start()
            def on_start(self, event):
                # TODO event not used, interrupted def outside init
                """

                :param event:
                :return:
                """
                self.interrupted = False
                self.set_message("Saying.")

            @on_message(r"Interrupt.$")
            def on_interrupt(self, event):
                # TODO event not used
                """

                :param event:
                :return:
                """
                self.set_message("Interrupted.")

            @on_message(r"Respectful.$")
            def on_respect(self, event):
                # TODO event not used
                """

                :param event:
                :return:
                """
                self.set_message("Good.")

        with task_messenger(TestTask) as m:
            # test for not solving it at all
            message = "Interrupt."
            m.send(message)
            blen = m.read()
            self.assertEqual(blen, 0)
            self.assertFalse(m.get_last_message() == "Interrupted.")
            m.send("Respectful.")
            blen = m.read()
            self.assertGreater(blen, 0)
            self.assertEqual(m.get_last_message(), 'Good.')
