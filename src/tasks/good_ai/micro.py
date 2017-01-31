import collections
import random
import string
import types

import attr
import six
from attr.validators import instance_of

from core.task import on_message, on_start, on_timeout
from tasks.competition.base import BaseTask


@attr.s
class TaskGenerator():
    '''
    instancer is a function which returns tuple of 2 or 3 elements which are:
        - str - instance of the task
        - iterable or function
            - either iterable of correct answers
            - or function which obtains answer and question and evaluates the answer and has to return True/False/None
            - if agent's answer is in iterable or function returns True, reward is 1
            - if agent's answer is not in iterable or function returns None, reward is 0
            - if function returns False, reward is -1
        - optionally it can return also the object which will override provide_feedback field (for the rest of generator lifetime)
    input_sep - str which is appended to task question. Defaults to ''
    provide_feedback can be bool, function, iterable, str or None
        - if bool
            - if True
                - if instancer answer is iterable - feedback is a random element of this iterbale
                - if instancer answer is a function - no feedback is shown
            - if False - feedback is not shown
        - if function - obtains bool, which signals if the answer was correct or not - has to return str, which is then shown
        - if iterable - random element from iterable is returned
        - if str - that str is shown
        - if None (default) - no feedback is shown
    feedback_sep - str which is appended to feedback (if it is provided and show_feedback_sep is True). Defaults to ''
    show_feedback_sep - if it is True, feedback separator is shown. If False, separator is not shown. Defaults to True
    '''
    instancer = attr.ib(validator=instance_of(types.FunctionType))
    input_sep = attr.ib(validator=instance_of(str), default='')
    provide_feedback = attr.ib(default=None)
    feedback_sep = attr.ib(validator=instance_of(str), default='')
    show_feedback_sep = attr.ib(validator=instance_of(bool), default=True)

    def get_task_instance(self):
        question, answer, *feedback = self.instancer(self)
        self.answer = answer
        if len(feedback) > 0:
            self.provide_feedback = feedback[0]
        question = question + self.input_sep
        return question, answer

    def get_feedback_text(self, correct):
        if self.provide_feedback is None or self.provide_feedback is False:
            return ''
        feedback = ''
        if callable(self.provide_feedback):
            feedback = self.provide_feedback(correct)
        if isinstance(self.provide_feedback, six.string_types):
            feedback = self.provide_feedback
        if isinstance(self.provide_feedback, collections.Iterable) and not isinstance(self.provide_feedback, six.string_types):  # strings are iterable too
            feedback = random.choice(self.provide_feedback)
        if self.provide_feedback is True and isinstance(self.answer, collections.Iterable):
            feedback = random.choice(self.answer)
        if self.show_feedback_sep:
            feedback = feedback + self.feedback_sep
        return feedback

    def check_answer(self, answer, question=None):
        '''
        Returns a tuple (answer_is_correct, reward)
        answer_is_correct - bool
        reward - int -1, 0 or 1
        '''
        if callable(self.answer):
            check = self.answer(answer, question)
            if check is None:
                return False, 0
            elif check is True:
                return True, 1
            else:
                return False, -1
        if answer in self.answer:
            return True, 1
        return False, 0


class MicroBase(BaseTask):

    def __init__(self, world=None):
        super(MicroBase, self).__init__(world=world, max_time=3000)
        self.tasker = self._get_task_generator()

    def _get_task_generator():
        pass

    @on_start()
    def give_instructions(self, event):
        self.question, self.check_answer = self.tasker.get_task_instance()
        self.set_message(self.question)

    @on_message(r'\.')
    def check_response(self, event):
        event.message = event.message.strip()[:-1]  # remove trailing whitespaces - temp. workaround
        correct = self.tasker.check_answer(event.message, self.question)
        feedback_text = self.tasker.get_feedback_text(correct) + '/'    # temp workaround so that feedback is never empty
        self.set_reward(1) if correct else self.set_reward(0)
        self.set_message(feedback_text)

    @on_timeout()
    def on_timeout(self, event):
        self.set_reward(0)


class Micro1Task(MicroBase):

    def _get_task_generator(self):
        def micro1_question(self):
            def micro1_reward(answer, question=''):
                if answer in string.ascii_lowercase:
                    return True
                elif answer == ' ':
                    return None
                else:
                    return False
            return random.choice(string.ascii_lowercase + ' '), micro1_reward
        return TaskGenerator(micro1_question)
