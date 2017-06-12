# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import unittest
import core.task as task


class TestEvents(unittest.TestCase):
    """

    """

    def testTriggers(self):
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

            @task.on_start()
            def start_handler(self, event):
                """

                :param event:
                :return:
                """
                pass

            @task.on_message()
            def message_handler(self, event):
                """

                :param event:
                :return:
                """
                pass

            @task.on_timeout()
            def timeout_handler(self, event):
                """

                :param event:
                :return:
                """
                pass

            @task.on_ended()
            def ended_handler(self, event):
                """

                :param event:
                :return:
                """
                pass

        tt = TestTask(max_time=10)
        triggers = tt.get_triggers()
        handlers = set(map(lambda t: t.event_handler, triggers))
        self.assertEqual(4, len(triggers))
        self.assertIn(self.get_func(TestTask.start_handler), handlers)
        self.assertIn(self.get_func(TestTask.message_handler), handlers)
        self.assertIn(self.get_func(TestTask.timeout_handler), handlers)
        self.assertIn(self.get_func(TestTask.ended_handler), handlers)
        types = dict((t.event_handler, t.type) for t in triggers)
        self.assertEqual(task.Start, types[self.get_func(TestTask.start_handler)])
        self.assertEqual(task.MessageReceived, types[self .get_func(TestTask.message_handler)])
        self.assertEqual(task.Timeout, types[self.get_func(TestTask.timeout_handler)])
        self.assertEqual(task.Ended, types[self.get_func(TestTask.ended_handler)])

    def testInheritance(self):
        """

        :return:
        """
        class BaseTask(task.Task):
            """

            """
            def __init__(self, *args, **kwargs):
                """

                :param args:
                :param kwargs:
                """
                super(BaseTask, self).__init__(*args, **kwargs)

            @task.on_start()
            def start_handler(self, event):
                """

                :param event:
                :return:
                """
                pass

        class ConcreteTask(BaseTask):
            """

            """
            def __init__(self, *args, **kwargs):
                """

                :param args:
                :param kwargs:
                """
                super(ConcreteTask, self).__init__(*args, **kwargs)


            @task.on_start()
            def start_handler(self, event):
                """ # overridden handler

                :param event:
                :return:
                """
                pass

        tt = ConcreteTask(max_time=10)
        triggers = tt.get_triggers()
        handlers = set(map(lambda t: t.event_handler, triggers))
        self.assertEqual(1, len(triggers))
        # The start_handler must be the one of the overridden task
        self.assertIn(self.get_func(ConcreteTask.start_handler), handlers)
        self.assertFalse(self.get_func(BaseTask.start_handler) in handlers)

    def testDynamicHandlers(self):
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

            @task.on_start()
            def start_handler(self, event):
                """

                :param event:
                :return:
                """
                def end_handler(self, event):
                    """

                    :param self:
                    :param event:
                    :return:
                    """
                    pass
                self.end_handler_func = end_handler
                self.add_handler(task.on_ended()(end_handler))

        triggers = []
        tt = TestTask(max_time=10)

        class EnvironmentMock():
            """

            """
            def __init__(self, triggers):
                """

                :param triggers:
                """
                self.triggers = triggers

            def raise_event(self, event):
                """ we only generate an init event

                :param event:
                :return:
                """
                tt.start_handler(event)

            def _register_task_trigger(self, task, trigger):
                """

                :param task:
                :param trigger:
                :return:
                """
                self.triggers.append(trigger)

        # raise the start event
        tt.start(EnvironmentMock(triggers))
        triggers.extend(tt.get_triggers())
        handlers = set(map(lambda t: t.event_handler, triggers))
        self.assertEqual(2, len(triggers))
        self.assertIn(self.get_func(TestTask.start_handler), handlers)
        self.assertIn(self.get_func(tt.end_handler_func), handlers)

    def get_func(self, method):
        """

        :param method:
        :return:
        """
        try:
            return method.im_func
        except AttributeError: # Python 3
            try:
                return method.__func__
            except AttributeError: # Python 3 (unbound method == func)
                return method


def main():
    unittest.main()

if __name__ == '__main__':
    main()
