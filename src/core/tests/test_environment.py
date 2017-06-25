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

import unittest
# TODO fix imports
import core.task as task
import core.environment as environment


class SerializerMock(object):
    """

    """
    pass


class SingleTaskScheduler:
    """

    """
    def __init__(self, task):
        """

        :param task:
        """
        self.task = task

    def get_next_task(self):
        """

        :return:
        """
        return self.task

    def reward(self, reward):
        # TODO static
        """

        :param reward:
        :return:
        """
        pass


class TestEnvironment(unittest.TestCase):
    """

    """

    def testRegistering(self):
        """

        :return:
        """
        class TestTask(task.Task):
            """

            """
            def __init__(self, *args, **kwargs):
                """

                :param args:
                :param kwargs:
                """
                super(TestTask, self).__init__(*args, **kwargs)
                self.handled = False

            @task.on_start()
            def start_handler(self, event):
                # TODO event not used
                """

                :param event:
                :return:
                """
                self.handled = True
        tt = TestTask(max_time=10)
        env = environment.Environment(SerializerMock(), SingleTaskScheduler(tt))
        tt.start(env)
        env._register_task_triggers(tt)
        # Start should be handled
        self.assertTrue(env.raise_event(task.Start()))
        # The start handler should have been executed
        self.assertTrue(tt.handled)
        env._deregister_task_triggers(tt)
        # Start should not be handled anymore
        self.assertFalse(env.raise_event(task.Start()))

    def testDynRegistering(self):
        """

        :return:
        """
        class TestTask(task.Task):
            """

            """
            def __init__(self, *args, **kwargs):
                """

                :param args:
                :param kwargs:
                """
                super(TestTask, self).__init__(*args, **kwargs)
                self.start_handled = False
                self.end_handled = False

            @task.on_start()
            def start_handler(self, event):
                """ End cannot be handled. # Start should be handled# The start handler should have been executed
                # Now the End should be handled# The end handler should have been executed# Start should not be
                handled anymore# End should not be handled anymore# Register them again! mwahaha (evil laugh) -- lol,
                 End should not be handled anymore/ Deregister them again! mwahahahaha (more evil laugh)
                :param event:
                :return:
                """
                try:
                    self.add_handler(task.on_ended()(self.end_handler.im_func))
                except AttributeError: # Python 3
                    self.add_handler(task.on_ended()(self.end_handler.__func__))
                self.start_handled = True

            def end_handler(self, event):
                # TODO event not used
                """

                :param event:
                :return:
                """
                self.end_handled = True

        tt = TestTask(max_time=10)
        env = environment.Environment(SerializerMock(), SingleTaskScheduler(tt))
        tt.start(env)
        env._register_task_triggers(tt)
        self.assertFalse(env.raise_event(task.Ended()))
        self.assertFalse(tt.end_handled)
        self.assertTrue(env.raise_event(task.Start()))
        self.assertTrue(tt.start_handled)
        self.assertTrue(env.raise_event(task.Ended()))
        self.assertTrue(tt.end_handled)
        env._deregister_task_triggers(tt)
        self.assertFalse(env.raise_event(task.Start()))
        tt.end_handled = False
        self.assertFalse(env.raise_event(task.Ended()))
        self.assertFalse(tt.end_handled)
        env._register_task_triggers(tt)
        self.assertFalse(env.raise_event(task.Ended()))
        self.assertFalse(tt.end_handled)
        env._deregister_task_triggers(tt)
        self.assertFalse(env.raise_event(task.Ended()))
        self.assertFalse(tt.end_handled)
