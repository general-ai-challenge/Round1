import random
import string
import unittest

from tasks.good_ai.micro import TaskGenerator


class TestTaskGenerator(unittest.TestCase):

    def test_instancer_iterable(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase
        tasker = TaskGenerator(micro1_question)

        question, answer = tasker.get_task_instance()
        check_correct_answer = tasker.check_answer('a')
        check_normal_answer = tasker.check_answer(' ')
        check_wrong_answer = tasker.check_answer('/')

        self.assertTrue(check_correct_answer[0])
        self.assertEqual(check_correct_answer[1], 1)
        self.assertFalse(check_normal_answer[0])
        self.assertEqual(check_normal_answer[1], -1)
        self.assertFalse(check_wrong_answer[0])
        self.assertEqual(check_wrong_answer[1], -1)

    def test_instancer_function(self):
        def micro1_question(self):
            def micro1_reward(answer, question=''):
                if answer in string.ascii_lowercase:
                    return True
                elif answer == ' ':
                    return None
                else:
                    return False
            return random.choice(string.ascii_lowercase + ' '), micro1_reward
        tasker = TaskGenerator(micro1_question)

        question, answer = tasker.get_task_instance()
        check_correct_answer = tasker.check_answer('a')
        check_normal_answer = tasker.check_answer(' ')
        check_wrong_answer = tasker.check_answer('/')

        self.assertTrue(check_correct_answer[0])
        self.assertEqual(check_correct_answer[1], 1)
        self.assertFalse(check_normal_answer[0])
        self.assertEqual(check_normal_answer[1], 0)
        self.assertFalse(check_wrong_answer[0])
        self.assertEqual(check_wrong_answer[1], -1)

    def test_input_separator_single_char(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '*')

        question, answer = tasker.get_task_instance()

        self.assertTrue(question.endswith('*'))

    def test_input_separator_string(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, 'now speak')

        question, answer = tasker.get_task_instance()

        self.assertTrue(question.endswith('now speak'))

    def test_feedback_true_iterable(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '', True)

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        for _ in range(10):
            self.assertTrue(feedback_text in answer)

    def test_feedback_true_function(self):
        def micro1_question(self):
            def micro1_answer(answer, question=None):
                return answer in string.ascii_lowercase + ' '
            return random.choice(string.ascii_lowercase + ' '), micro1_answer
        tasker = TaskGenerator(micro1_question, '', True)

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertEqual(feedback_text, '')

    def test_feedback_false(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '', False)

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertEqual(feedback_text, '')

    def test_feedback_none(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '', None)

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertEqual(feedback_text, '')

    def test_feedback_function(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '

        def micro1_feedback(correct, question):
            return "nice" if correct else "bad :("
        tasker = TaskGenerator(micro1_question, '', micro1_feedback)

        question, answer = tasker.get_task_instance()
        feedback_text_correct = tasker.get_feedback_text(True)
        feedback_text_incorrect = tasker.get_feedback_text(False)

        self.assertEqual(feedback_text_correct, 'nice')
        self.assertEqual(feedback_text_incorrect, 'bad :(')

    def test_feedback_iterable(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        valid_feedbacks = ['great', 'nice', 'awesome']
        tasker = TaskGenerator(micro1_question, '', valid_feedbacks)

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertIn(feedback_text, valid_feedbacks)

    def test_feedback_str(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '', "awesome")

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertEqual(feedback_text, "awesome")

    def test_instancer_feedback_override(self):
        def micro1_question(self):
            def micro1_feedback(correct, question):
                return "nice" if correct else "bad :("
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' ', micro1_feedback
        tasker = TaskGenerator(micro1_question, '', None)

        question, answer = tasker.get_task_instance()
        feedback_text_correct = tasker.get_feedback_text(True)
        feedback_text_incorrect = tasker.get_feedback_text(False)

        self.assertEqual(feedback_text_correct, 'nice')
        self.assertEqual(feedback_text_incorrect, 'bad :(')

    def test_feedback_sep_with_feedback(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '', "awesome", '!')

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertTrue(feedback_text.endswith('awesome!'))

    def test_feedback_sep_no_feedback(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '', False, '!')

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertFalse(feedback_text.endswith('!'))

    def test_show_feedback_sep_false(self):
        def micro1_question(self):
            return random.choice(string.ascii_lowercase + ' '), string.ascii_lowercase + ' '
        tasker = TaskGenerator(micro1_question, '', "awesome", '!', False)

        question, answer = tasker.get_task_instance()
        feedback_text = tasker.get_feedback_text(True)

        self.assertTrue(feedback_text.endswith('awesome'))
