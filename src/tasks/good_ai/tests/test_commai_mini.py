import unittest

from tasks.competition.tests.helpers import task_messenger
import tasks.good_ai.comm_ai_mini as comm_ai_mini

from worlds.grid_world import GridWorld


class TestCommAIMiniBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if cls is TestCommAIMiniBase:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")
        super(TestCommAIMiniBase, cls).setUpClass()

    def __init__(self, *args, **kwargs):
        super(TestCommAIMiniBase, self).__init__(*args, **kwargs)
        self.task_set = None

    def _obtains_feedback(self, m):
        feedback_len = m.read()
        self.assertGreater(feedback_len, 0)

    def test_new_correct(self):
        with task_messenger(self.task_set, GridWorld) as m:
            m.read()
            correct_answer = m._env._task_scheduler.task.answer + '.'
            m.send(correct_answer)

            self._obtains_feedback(m)

            m.send()
            self.assertEqual(m.get_cumulative_reward(), 1)

    def test_new_timeout(self):
        with task_messenger(self.task_set, GridWorld) as m:
            m.read()
            while m.is_silent():
                m.send()

            self._obtains_feedback(m)
            feedback = m.get_last_message()
            self.assertTrue('Wrong' in feedback)

            m.send()
            self.assertEqual(m.get_cumulative_reward(), 0)

    def test_error_answer(self):
        with task_messenger(self.task_set, GridWorld) as m:
            m.read()
            m.send("wrong answer.")

            self._obtains_feedback(m)
            feedback = m.get_last_message()
            self.assertTrue('Wrong' in feedback)

            m.send()
            self.assertEqual(m.get_cumulative_reward(), 0)


class TestCommAIMiniTS1(TestCommAIMiniBase):

    def __init__(self, *args, **kwargs):
        super(TestCommAIMiniTS1, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet1


class TestCommAIMiniTS2(TestCommAIMiniBase):

    def __init__(self, *args, **kwargs):
        super(TestCommAIMiniTS2, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet2


class TestCommAIMiniTS3(TestCommAIMiniBase):

    def __init__(self, *args, **kwargs):
        super(TestCommAIMiniTS3, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet3


class TestCommAIMiniTS4(TestCommAIMiniBase):

    def __init__(self, *args, **kwargs):
        super(TestCommAIMiniTS4, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet4


class TestCommAIMiniTS5(TestCommAIMiniBase):

    def __init__(self, *args, **kwargs):
        super(TestCommAIMiniTS5, self).__init__(*args, **kwargs)
        self.task_set = comm_ai_mini.TaskSet5
