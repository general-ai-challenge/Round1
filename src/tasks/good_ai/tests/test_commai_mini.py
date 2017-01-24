import unittest
from functools import wraps

from tasks.competition.tests.helpers import task_messenger
import tasks.good_ai.comm_ai_mini as comm_ai_mini

from worlds.grid_world import GridWorld


def use_messages(fun):
    @wraps(fun)
    def decorated_fun(self):
        with task_messenger(comm_ai_mini.TaskSet1, GridWorld) as m:
            m.read()
            fun(self, m)
    return decorated_fun


def get_reward(val):
    def decorator_reward(fun):
        @wraps(fun)
        def decorated_fun(self, m):
            fun(self, m)
            m.send()
            self.assertEqual(m.get_cumulative_reward(), val)
        return decorated_fun
    return decorator_reward


class TestCommAIMiniTS1(unittest.TestCase):

    def _obtains_feedback(self, m):
        feedback_len = m.read()
        self.assertGreater(feedback_len, 0)

    @use_messages
    @get_reward(1)
    def test_new_correct(self, m):
        correct_answer = m._env._task_scheduler.task.answer + '.'
        m.send(correct_answer)

        self._obtains_feedback(m)

    @use_messages
    @get_reward(0)
    def test_new_timeout(self, m):
        while m.is_silent():
            m.send()

        self._obtains_feedback(m)
        feedback = m.get_last_message()
        self.assertTrue('Wrong' in feedback)

    @use_messages
    @get_reward(0)
    def test_error_answer(self, m):
        m.send("wrong answer.")

        self._obtains_feedback(m)
        feedback = m.get_last_message()
        self.assertTrue('Wrong' in feedback)
