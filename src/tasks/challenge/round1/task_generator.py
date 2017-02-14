# Copyright (c) 2017-present, GoodAI
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import collections
import types
import random

import attr
import six
from attr.validators import instance_of


@attr.s
class TaskGenerator(object):
    '''
    instancer is a function which returns tuple of 2 or 3 elements which are:
        - str - instance of the task
        - iterable or function
            - either iterable of correct answers
            - or function which obtains answer and question and evaluates the answer and has to return True/False/None
            - if agent's answer is in iterable or function returns True, reward is 1
            - if agent's answer is not in iterable or function returns False, reward is -1 (i.e. punishement)
            - if function returns None, reward is 0
        - optionally it can return also the object which will override provide_feedback field (for the rest of generator lifetime)
    input_sep - str which is appended to task question. Defaults to ''
    provide_feedback can be bool, function, iterable, str or None
        - if bool
            - if True
                - if instancer answer is iterable - feedback is a random element of this iterbale
                - if instancer answer is a function - no feedback is shown
            - if False - feedback is not shown
        - if function - obtains bool, which signals if the answer was correct or not and the original question- has to return str, which is then shown
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
        items = list(self.instancer(self))
        question, answer = items[0], items[1]
        self.answer = answer
        if len(items) > 2:
            self.provide_feedback = items[2]
        question = question + self.input_sep
        return question, answer

    def get_feedback_text(self, correct, question=None):
        if self.provide_feedback is None or self.provide_feedback is False:
            return ''
        feedback = ''
        if callable(self.provide_feedback):
            feedback = self.provide_feedback(correct, question)
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
        Returns a triple (task_finished, answer_is_correct, reward)
        task_finished - bool
        answer_is_correct - bool
        reward - int -1, 0 or 1
        '''
        if callable(self.answer):
            check, reward = self.answer(answer, question)
            if check is None:
                return False, False, reward
            elif check is True:
                return True, True, reward
            else:
                return True, False, reward
        if answer in self.answer:
            return True, True, 1
        else:
            return True, False, -1

    def get_original_question(self, question):
        input_sep_len = len(self.input_sep)
        if (input_sep_len > 0):  # because using -0 is same as 0 which makes string empty
            return question[:-input_sep_len]
        return question
