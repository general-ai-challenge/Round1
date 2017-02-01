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
        else:
            return False, -1

    def get_original_question(self, question):
        input_sep_len = len(self.input_sep)
        if (input_sep_len > 0):  # because using -0 is same as 0 which makes string empty
            return question[:-input_sep_len]
        return question


class MicroBase(BaseTask):

    def __init__(self, world=None):
        super(MicroBase, self).__init__(world=world, max_time=3000)
        self.tasker = self._get_task_generator()

    def _get_task_generator():
        pass

    def get_original_question(self, question):
        return self.tasker.get_original_question(question)

    @on_start()
    def give_instructions(self, event):
        self.question, self.check_answer = self.tasker.get_task_instance()
        self.set_message(self.question)

    @on_message(r'\.')
    def check_response(self, event):
        event.message = event.message.strip()[:-1]  # remove trailing whitespaces - temp. workaround
        correct, reward = self.tasker.check_answer(event.message, self.question)
        feedback_text = self.tasker.get_feedback_text(correct, self.question)
        if len(feedback_text) == 0:
            feedback_text = feedback_text + '/'    # temp workaround so that feedback is never empty
        self.set_reward(reward)
        self.set_message(feedback_text)

    @on_timeout()
    def on_timeout(self, event):
        self.set_reward(0)


class Micro1Task(MicroBase):

    def _get_task_generator(self):
        def micro1_question(self):
            def micro1_reward(answer, question=''):
                if answer == ' ':
                    return None
                return answer in string.ascii_lowercase
            return random.choice(string.ascii_lowercase + ' '), micro1_reward
        return TaskGenerator(micro1_question)


class MicroMappingTask(MicroBase):

    task_gen_kwargs = {}

    def _get_mapping(self):
        pass

    def _get_task_generator(self):
        mapping = self._get_mapping()

        def micro_mapping_question(self):
            def micro_mapping_reward(answer, question):
                key = self.get_original_question(question)
                return answer == mapping[key]
            return random.choice(list(mapping.keys())), micro_mapping_reward
        return TaskGenerator(micro_mapping_question, **self.task_gen_kwargs)


class Micro2Task(MicroMappingTask):

    def _get_mapping(self):
        correct_answer = random.choice(string.ascii_lowercase)
        mapping = {x: correct_answer for x in string.ascii_lowercase}
        for c in '!":?.,;':
            mapping[c] = c
        return mapping


class Micro3Task(MicroMappingTask):

    def _get_mapping(self):
        alphabet = string.ascii_lowercase + ' '
        mapping = dict(zip(alphabet, alphabet))
        return mapping


class Micro4Task(MicroMappingTask):

    def _get_mapping(self):
        permutation = ''.join(random.sample(string.ascii_lowercase, len(string.ascii_lowercase)))
        mapping = dict(zip(string.ascii_lowercase, permutation))
        for c in '!":?.,;':
            mapping[c] = c
        return mapping


class Micro5Sub1Task(MicroMappingTask):
    task_gen_kwargs = {}

    def _get_mapping(self):
        numbers = '0123456789'
        permutation = ''.join(random.sample(numbers, len(numbers)))
        mapping = dict(zip(numbers, permutation))

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


class Micro5Sub2Task(Micro5Sub1Task):
    task_gen_kwargs = {'feedback_sep': '!'}


class Micro5Sub3Task(Micro5Sub1Task):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': '!'}


def random_string_from(length, subset):
    return "".join(random.choice(subset) for _ in range(length))


# TODO: example (also 5.5 and 5.6) shows one space between question and
# the feedback, but the description does not mention it - this is version
# without the space
class Micro5Sub4Task(MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': '!'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random_string_from(2, numbers) for x in numbers}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


# TODO: trailing dots in the answer is ignored by CommAI-env
# TODO: I will try to refactor following classes ASAP. I just need to see them all in order to make proper decisions- MV
class Micro5Sub5Task(MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': '!'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


class Micro5Sub6Task(MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': '!'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            if is_correct:
                return mapping[key][:-1]    # remove trailing dot
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


class Micro5Sub7Task(MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': '!'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {}
        for x in numbers:
            answer_len = random.choice([1, 2])
            answer = random_string_from(answer_len, numbers)
            mapping[x] = answer + '.'

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            if is_correct:
                return mapping[key][:-1]    # remove trailing dot
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


class Micro5Sub8Task(MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': '!'}

    def _get_mapping(self):
        numbers = '0123456789'
        nr_questions = 10
        questions = [random_string_from(2, numbers) for _ in range(nr_questions)]
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            if is_correct:
                return mapping[key][:-1]    # remove trailing dot
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping
