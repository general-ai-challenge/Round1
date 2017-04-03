# Copyright (c) 2017-present, GoodAI
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import os
import random
import re
import string
from contextlib import contextmanager

from core.task import Task
from core.task import on_message, on_start, on_timeout
from tasks.challenge.round1.task_generator import TaskGenerator

DICTIONARY_FILE = 'res/dict_gsl.txt'
REQUIRED_CONSECUTIVE_REWARDS = 10   # more or less arbitrary constant; high enough to prevent random solutions


class MicroBase(Task):
    reg_answer_end = r'.'
    FAILED_TASK_TOLERANCE = 1.0
    SUCCESS_TOLERANCE = 4.0
    tasker = None

    def __init__(self, world=None):
        super(MicroBase, self).__init__(world=world, max_time=10000)
        self.skip_task_separator = True

    def get_task_generator(self):
        pass

    def agent_solved_instance_under_time_limit(self):
        '''
        Checks whether the agent solved task instance successfully
        '''
        return self.under_time_limit_for_successfull_solution() and self.agent_solved_instance()

    def agent_solved_instance(self):
        '''
        Checks whether the agent solved task instance
        '''
        return self.consecutive_reward >= REQUIRED_CONSECUTIVE_REWARDS

    def agent_should_know_answers(self):
        '''
        Checks whether the information provided to agent was sufficient for it to know the correct solution to task instance
        Tasks may override this method - this is equal to knowing all the correct answers from first step
        '''
        return True

    def under_time_limit_for_successfull_solution(self):
        '''
        Checks whether the task is still in stage, where agent can successfully solve the task.
        This method does not check whether agent actually solved the task! Only if the time for the solution ran up or not!
        '''
        if self.max_questions_for_success:
            return self.questions_asked <= self.max_questions_for_success
        else:
            return True

    def get_original_question(self, question):
        return self.tasker.get_original_question(question)

    @on_start()
    def new_task_instance(self, event):
        self.tasker = self.get_task_generator()
        self.questions_asked = 0
        self.consecutive_reward = 0
        self.max_questions_nr = None
        self.max_questions_for_success = None
        self.agent_answer = ''
        self.give_instructions()

    def preprocess_answer(self, message):
        self.agent_answer += message[-1]    # add the newest char

    def provide_reward(self, reward):
        if reward > 0:
            self.consecutive_reward += 1
        elif reward < 0:
            self.consecutive_reward = 0
        self.set_immediate_reward(reward)

    def question_answered(self, is_correct):
        self.questions_asked += 1

    def check_if_task_instance_finished(self):
        if self.agent_solved_instance_under_time_limit():    # agent solved instance in time
            self.set_result(True, provide_result_as_reward=False)
            return True

        if self.agent_solved_instance():    # agent solved instance too late
            self.set_result(False, provide_result_as_reward=False)
            return True

        if not self.max_questions_for_success and self.agent_should_know_answers():  # agent did not solve it but should know answers from now on
            self.max_questions_for_success = self.questions_asked + REQUIRED_CONSECUTIVE_REWARDS * (1.0 + self.SUCCESS_TOLERANCE)

        if not self.max_questions_nr and not self.under_time_limit_for_successfull_solution():  # agent failed but give him some time to learn task
            self.max_questions_nr = self.questions_asked * (1.0 + self.FAILED_TASK_TOLERANCE)

        if self.max_questions_nr and self.questions_asked > self.max_questions_nr:  # agent used up all the extra time
            self.set_result(False, provide_result_as_reward=False)
            self._raise_timeout()
            return True
        return False

    def provide_feedback(self, correct):
        feedback_text = self.tasker.get_feedback_text(correct, self.question)
        self.set_message(feedback_text)

    def give_instructions(self):
        self.question, self.check_answer = self.tasker.get_task_instance()
        self.set_message(self.question)
        # internal buffer reset
        self.agent_answer = ''
        self.remaining_instruction_length = len(self.question)

    @on_message()   # on every character
    def check_response(self, event):
        self.remaining_instruction_length -= 1

        if not self._env.is_silent():
            if not event.message[-1] == ' ':
                self.set_immediate_reward(-1)
            return

        if self.remaining_instruction_length > 1:
            return

        self.preprocess_answer(event.message)

        if not self._answer_ended(self.agent_answer):
            return      # agent is still speaking - do not check it yet

        answer = self.agent_answer # no stripping of agent's answer

        finished, correct, reward = self.tasker.check_answer(answer, self.question)
        self.provide_reward(reward)

        # if one task sub-instance solved
        if finished:
            self.question_answered(correct)
            self.provide_feedback(correct)
            if not self.check_if_task_instance_finished():
                # give next instruction
                self.give_instructions()

    @on_timeout()   # while we use checking if agent solved instance ASAP - can this actually happen?
    def end_task_instance(self, event):
        self.set_result(False, provide_result_as_reward=False)

    @staticmethod
    def is_prefix(answer, correct_answer):
        if len(answer) >= len(correct_answer):
            return False
        return correct_answer.startswith(answer)

    def _answer_ended(self, message):
        return not (re.search(self.reg_answer_end, message, re.DOTALL) is None)


class Micro1Task(MicroBase):
    ALPHABET_SIZE = 10

    def __init__(self):
        self.base_alphabet = string.ascii_letters + string.digits + ' ,.!;?-'
        super(Micro1Task, self).__init__()

    @on_start()
    def micro1_on_start(self, event):
        self.alphabet = random.sample(self.base_alphabet, self.ALPHABET_SIZE)
        self.remaining_options = len(self.base_alphabet)
        self.should_know = False

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro1Task, self).question_answered(is_correct)
        if is_correct or self.remaining_options == 0:
            self.should_know = True
        if not is_correct:
            self.remaining_options -= 1

    def get_task_generator(self):
        alphabet = self.alphabet
        correct_answer = random.choice(alphabet)

        def micro1_question(self):
            return random.choice(alphabet), correct_answer
        return TaskGenerator(micro1_question)


def random_string_from(length, subset):
    return "".join(random.choice(subset) for _ in range(length))


def random_strings_from(charset, nr_of_strings, string_len_options=None, append=''):
    string_len_options = string_len_options or [1]
    result = []
    for _ in range(nr_of_strings):
        answer_len = random.choice(string_len_options)
        answer = random_string_from(answer_len, charset)
        result.append(answer + append)
    return result


class MicroMappingTask(MicroBase):

    task_gen_kwargs = {}

    def agent_should_know_answers(self):
        if len(self.known_mapping) > 0:
            return self.should_know
        else:
            return True

    def _get_mapping_options(self, mapping):
        '''
        This method is optional but if implemented, it should return dictionary where keys are all possible questions for agent and value is number of possible
        answers on that question from which agent has to find the right one.
        If mapping does not want to implement "agent_should_know_answers" it can implement this method and MicroMapping will use its "agent_should_know_answers"
        mechanism.
        '''
        return {}

    def _get_mapping(self):
        pass

    def question_answered(self, is_correct):
        super(MicroMappingTask, self).question_answered(is_correct)
        if len(self.known_mapping) == 0:    # not all Mapping tasks use the all_mapping_options concept
            return
        if self.question[-1] == '.' and len(self.question) > 1:
            question = self.question[:-1]
        else:
            question = self.question
        if is_correct:
            self.known_mapping[question] = 1
        else:
            self.known_mapping[question] = max(self.known_mapping[question] - 1, 1)

        if all(x == 1 for x in self.known_mapping.values()):
            self.should_know = True

    def get_task_generator(self):
        mapping = self._get_mapping()
        self.known_mapping = self._get_mapping_options(mapping)
        self.should_know = False

        def multigen(d):
            while True:
                k = list(d.keys()) * len(d.keys())
                random.shuffle(k)
                for i in k:
                    yield i
        gen = multigen(mapping)

        def micro_mapping_question(self):
            def micro_mapping_reward(answer, question):
                key = self.get_original_question(question)
                if len(answer) > 0 and MicroBase.is_prefix(answer, mapping[key]):
                    return None, 0
                if len(answer) < len(mapping[key]):
                    return None, 0
                correct = answer == mapping[key]
                return correct, 1 if correct else -1
            return next(gen), micro_mapping_reward
        return TaskGenerator(micro_mapping_question, **self.task_gen_kwargs)

    # this could be solved by less code, but I chose the explicit way
    def _get_simple_feedback_provider(self, mapping):
        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            return mapping[key]
        return feedback_provider

    def _get_prepend_feedback_provider(self, mapping, prepend_set, prepend_len_options=None):
        prepend_len_options = prepend_len_options or [1]

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            prepend_len = random.choice(prepend_len_options)
            prepend = random_string_from(prepend_len, prepend_set)
            return prepend + mapping[key]
        return feedback_provider


class Micro2Task(MicroMappingTask):
    ALPHABET_SIZE = 4
    base_alphabet = string.ascii_lowercase

    def __init__(self):
        super(Micro2Task, self).__init__()

    @on_start()
    def micro2_on_start(self, event):
        self.alphabet = random.sample(self.base_alphabet, self.ALPHABET_SIZE)
        self.remaining_options = len(self.base_alphabet)

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro2Task, self).question_answered(is_correct)
        if (is_correct and self.question in self.alphabet) or self.remaining_options == 0:
            self.should_know = True
        if not is_correct:
            self.remaining_options -= 1

    def _get_mapping(self):
        correct_answer = random.choice(self.alphabet)
        mapping = {x: correct_answer for x in self.alphabet}
        for c in ' !":?.,;':
            mapping[c] = c
        return mapping


class Micro3Task(MicroMappingTask):
    ALPHABET_SIZE = 4
    base_alphabet = string.ascii_lowercase

    @on_start()
    def micro3_on_start(self, event):
        self.alphabet = random.sample(self.base_alphabet, self.ALPHABET_SIZE)

    def _get_mapping_options(self, mapping):
        result = {x: len(self.base_alphabet) for x in self.alphabet}
        for c in ' !":?.,;':
            result[c] = 1
        return result

    def _get_mapping(self):
        permutation = ''.join(random.sample(self.alphabet, len(self.alphabet)))
        mapping = dict(zip(self.alphabet, permutation))
        for c in ' !":?.,;':
            mapping[c] = c
        return mapping


class Micro4Task(MicroMappingTask):
    ALPHABET_SIZE = 4

    @on_start()
    def micro4_on_start(self, event):
        self.alphabet = random.sample(string.ascii_lowercase + ' !":?.,;', self.ALPHABET_SIZE)

    def _get_mapping(self):
        alphabet = self.alphabet
        mapping = dict(zip(alphabet, alphabet))
        return mapping


class FeedbackMappingTaskMixin(MicroMappingTask):
    '''
    This mixin should be used when the task uses feedback and we assume the feedback can be exploited already.
    The only one occurrence is needed for every key from mapping.
    '''

    def _get_mapping_options(self, mapping):
        keys = mapping.keys()
        return {x: 2 for x in keys}


class Micro5Sub1Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {}

    def _get_mapping(self):
        numbers = string.digits
        permutation = ''.join(random.sample(numbers, len(numbers)))
        mapping = dict(zip(numbers, permutation))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub2Task(Micro5Sub1Task):
    task_gen_kwargs = {'feedback_sep': ';'}


class Micro5Sub3Task(Micro5Sub1Task):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}


class Micro5Sub4Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        mapping = {x: random_string_from(2, numbers) for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub5Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub6Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            if is_correct:
                return mapping[key][:-1]    # remove trailing dot
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


class Micro5Sub7Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        answers = random_strings_from(numbers, len(numbers), [1, 2], '.')
        mapping = dict(zip(numbers, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub8Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}
    MAPPING_SIZE = 10

    def _get_mapping(self):
        numbers = string.digits
        questions = random_strings_from(numbers, self.MAPPING_SIZE, [2])
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub9Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}
    MAPPING_SIZE = 10

    def _get_mapping(self):
        numbers = string.digits
        questions = random_strings_from(numbers, self.MAPPING_SIZE, [1, 2])
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# TODO: should be the ignored part be always the same for the same inputs or can it change? - this version changes it
class Micro5Sub10Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_prepend_feedback_provider(mapping, numbers)
        return mapping


class Micro5Sub11Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            do_prepend = random.choice([True, False])
            if do_prepend:
                prepend = random.choice(numbers)
            else:
                prepend = ''
            return prepend + mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


# stems from 5.7
# TODO: description says "either 3 or 4 or 5 chars. Shown example for 3
# chars". So will it be always the same size of feedback for on task
# instance? Or can it be mixed? - this version is mixed
# same question for 5.13, 5.14, 5.15, 5.16, 5.17 and 5.18
class Micro5Sub12Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        answers = random_strings_from(numbers, len(numbers), [3, 4, 5], '.')
        mapping = dict(zip(numbers, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# stems from 5.9
class Micro5Sub13Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}
    MAPPING_SIZE = 10

    def _get_mapping(self):
        numbers = string.digits
        questions = random_strings_from(numbers, self.MAPPING_SIZE, [3, 4, 5])
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# stems from 5.12
class Micro5Sub14Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_prepend_feedback_provider(mapping, numbers, [2, 3, 4])
        return mapping


class Micro5Sub15Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = string.digits
        answers = random_strings_from(numbers, len(numbers), range(1, 6), '.')
        mapping = dict(zip(numbers, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub16Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}
    MAPPING_SIZE = 10

    def _get_mapping(self):
        numbers = string.digits
        questions = random_strings_from(numbers, self.MAPPING_SIZE, range(1, 6))
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub17Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}
    MAPPING_SIZE = 10

    def _get_mapping(self):
        numbers = string.digits
        questions = random_strings_from(numbers, self.MAPPING_SIZE, range(1, 6))
        answers = random_strings_from(numbers, len(questions), range(1, 6), '.')
        mapping = dict(zip(questions, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# stems from 5.17
class Micro5Sub18Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}
    MAPPING_SIZE = 10

    def _get_mapping(self):
        numbers = string.digits
        questions = random_strings_from(numbers, self.MAPPING_SIZE, range(1, 11))
        answers = random_strings_from(numbers, len(questions), range(1, 11), '.')
        mapping = dict(zip(questions, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


def load_dictionary(file_name):
    current_dir = os.path.dirname(__file__)
    file_path = os.path.join(current_dir, '../../../' + file_name)
    with open(file_path) as f:
        content = f.readlines()

    return [x.strip() for x in content
            if not any(map(lambda forbidden: forbidden in x.strip(), load_dictionary.forbidden_strings))]

load_dictionary.forbidden_strings = []


class Micro6Task(MicroBase):
    reg_answer_end = r'\.'
    MAPPING_SIZE = 8
    FAILED_TASK_TOLERANCE = 2.0

    @on_start()
    def new_task_instance(self, event):
        super(Micro6Task, self).new_task_instance(event)
        self.should_know = False
        self.actual_key = ''

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro6Task, self).question_answered(is_correct)
        key = self.question.split()[-1].split('.')[0]
        self.mapping_check[key] = True
        if all(self.mapping_check.values()):
            self.should_know = True

    def get_task_generator(self):
        content = load_dictionary(DICTIONARY_FILE)
        vocabulary = content[:200]
        mapping = dict(zip(random.sample(vocabulary, self.MAPPING_SIZE),
                           random.sample(vocabulary, self.MAPPING_SIZE)))
        keys = list(mapping.keys())
        self.mapping_check = {key: False for key in keys}

        def micro6_question(self):
            def micro6_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            self.key_idx = random.randint(0, len(keys) - 1)
            word1 = keys[self.key_idx]
            word2 = mapping[word1]
            question = 'random_map: ' + word1 + '.'
            sentence = word2 + '.'
            return question, [sentence], micro6_feedback

        return TaskGenerator(micro6_question, '', None, ';')


@contextmanager
def forbid_dictionary_strings(words):
    load_dictionary.forbidden_strings = words
    yield
    load_dictionary.forbidden_strings = []


class Micro7Sub1Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro7_1_question(self):
            correct_answer = random.choice(string.ascii_lowercase) + '.'
            question = "say: {}".format(correct_answer)

            def micro7_1_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '! ' + correct_answer
            return question, [correct_answer], micro7_1_feedback
        return TaskGenerator(micro7_1_question, '', None, ';')


class Micro7Sub2Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        valid_words = load_dictionary(DICTIONARY_FILE)

        def micro7_2_question(self):
            word = random.choice(valid_words) + '.'
            question = "say: {}".format(word)

            def micro7_2_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '! ' + word
            return question, [word], micro7_2_feedback
        return TaskGenerator(micro7_2_question, '', None, ';')


class Micro7Sub3Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        valid_words = load_dictionary(DICTIONARY_FILE)

        def micro7_3_question(self):
            sentence = random.choice(valid_words) + ' ' + random.choice(valid_words) + '.'
            question = "say: {}".format(sentence)

            def micro7_3_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '! ' + sentence
            return question, [sentence], micro7_3_feedback
        return TaskGenerator(micro7_3_question, '', None, ';')


class Micro8Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro8_question(self):
            alphabet = string.ascii_lowercase
            sentence = "{}{}{}{}{}.".format(' ' * random.randint(0, 6), random.choice(alphabet), ' ' * random.randint(0, 6),
                                            random.choice(alphabet), ' ' * random.randint(0, 6))
            question = "say: {}".format(sentence)
            sentence = re.sub(' +', ' ', sentence).strip()

            def micro8_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '! ' + sentence
            return question, [sentence], micro8_feedback

        return TaskGenerator(micro8_question, '', None, ';')


class Micro9Sub1Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro9_1_question(self):
            valid_words = string.ascii_lowercase
            word = random.choice(valid_words) + '.'
            question = "spell: {}".format(word)
            sentence = " ".join(word)

            def micro9_1_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                return reaction + '! ' + sentence
            return question, [sentence], micro9_1_feedback
        return TaskGenerator(micro9_1_question, '', None, ';')


class Micro9Sub2Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro9_2_question(self):
            valid_words = load_dictionary(DICTIONARY_FILE)
            word = random.choice(valid_words) + '.'
            question = "spell: {}".format(word)
            sentence = " ".join(word)

            def micro9_2_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                return reaction + '! ' + sentence

            return question, [sentence], micro9_2_feedback

        return TaskGenerator(micro9_2_question, '', None, ';')


class Micro9Sub3Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro9_3_question(self):
            valid_words = load_dictionary(DICTIONARY_FILE)
            word = random.choice(valid_words)
            joint = random.choice(['-', '#', ','])
            question = "interleave: " + word + ' by ' + joint + '.'
            sentence = joint.join(word) + '.'

            def micro9_3_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                return reaction + '! ' + sentence

            return question, [sentence], micro9_3_feedback

        return TaskGenerator(micro9_3_question, '', None, ';')


class Micro10Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro10_question(self):
            valid_words = load_dictionary(DICTIONARY_FILE)
            n = random.randint(2, 3)
            questions = []
            words = []
            for i in range(0, n):
                word = random.choice(valid_words)
                words.append(word)
                questions.append('say: {}'.format(word))
            question = ' '.join(questions) + '.'
            sentence = ' '.join(words) + '.'

            def micro10_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro10_feedback
        return TaskGenerator(micro10_question, '', None, ';')


class Micro11Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro11_question(self):
            actions = ['reverse', 'concatenate', 'interleave']
            action = random.choice(actions)
            valid_words = ["ab", "ac", "ad", "bc", "bd", "cd"]
            questions = []
            words = []
            for i in range(0, 2):
                word = random.choice(valid_words)
                words.append(word)
                questions.append('say: {}'.format(word))
            question = ' '.join(questions) + ' ' + action + ':.'
            if action == 'reverse':
                words.reverse()
                sentence = ' '.join(words)
            elif action == 'concatenate':
                sentence = ''.join(words)
            else:
                sentence = [val for pair in zip(words[0], words[1]) for val in pair]
                sentence = ''.join(sentence)
            sentence += '.'

            def micro11_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro11_feedback
        return TaskGenerator(micro11_question, '', None, ';')


class Micro12Task(MicroBase):
    reg_answer_end = r'\.'

    @staticmethod
    def string_special_union(str1, str2):
        if str1.find(str2) >= 0:
            return str1
        return str1 + str2

    @staticmethod
    def string_special_exclude(str1, str2):
        return str1.replace(str2, '')

    def get_task_generator(self):
        def micro12_question(self):
            actions = ['union', 'exclude']
            action = random.choice(actions)
            valid_words = ["abc", "acd", "adc", "bcd", "bda", "cdb"]
            valid_second_words = ["a", "b", "c", "d"]
            word = random.choice(valid_words)
            second_word = random.choice(valid_second_words)
            question = 'say: {} say: {} {}:.'.format(word, second_word, action)
            if action == 'union':
                sentence = Micro12Task.string_special_union(word, second_word)
            else:
                sentence = Micro12Task.string_special_exclude(word, second_word)
            sentence += '.'

            def micro12_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro12_feedback
        return TaskGenerator(micro12_question, '', None, ';')


class Micro13Sub1Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro13_1_question(self):
            def micro13_1_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            action = random.randint(1, 4)
            words = list('abcde')
            # and
            if action == 1:
                word1 = random.choice(words)
                word2 = random.choice(words)
                question = ' say: {} and {}.'.format(word1, word2)
                sentence = '{}{}.'.format(word1, word2)
                return question, sentence, micro13_1_feedback
            # or
            elif action == 2:
                word1 = random.choice(words)
                word2 = random.choice(words)
                question = ' say: {} or {}.'.format(word1, word2)
                sentence = '{}.'.format(random.choice([word1, word2]))

                def or_reward(answer, question=''):
                    answer_ = answer[:-1]
                    correct = answer_ == word1 or answer_ == word2 or answer_ == word1 + word2 or answer_ == word2 + word1
                    return correct, 1 if correct else -1
                return question, or_reward, micro13_1_feedback
            # anything and not
            elif action == 3:
                word1 = 'anything'
                word2 = random.choice(words)
                words.remove(word2)
                question = ' say: {} and not {}.'.format(word1, word2)
                sentence = random.choice(words)

                def anything_and_not_reward(answer, question=''):
                    correct = answer.find(word2) < 0 and len(answer) > 1
                    return correct, 1 if correct else -1
                return question, anything_and_not_reward, micro13_1_feedback
            # or but not
            else:
                word1 = random.choice(words)
                words.remove(word1)
                word2 = random.choice(words)
                words.remove(word2)
                word3 = random.choice([word1, word2, random.choice(words)])
                question = ' say: {} or {} but not {}.'.format(word1, word2, word3)
                correct_word = [word1, word2]
                if word3 in correct_word:
                    correct_word.remove(word3)
                sentence = random.choice(correct_word)

                def or_but_not_reward(answer, question=''):
                    answer_ = answer[:-1]
                    correct = answer_ == word1 or answer_ == word2 or answer_ == word1 + word2 or answer_ == word2 + word1
                    correct = correct and (answer.find(word3) < 0)
                    return correct, 1 if correct else -1
                return question, or_but_not_reward, micro13_1_feedback
        return TaskGenerator(micro13_1_question, '', None, ';')


class Micro13Sub2Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro13_2_question(self):
            def micro13_2_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            alphabet = string.ascii_lowercase
            actions = ['or', 'and']
            action = random.choice(actions)
            operands = random.randint(2, 4)
            words = []
            for i in range(operands):
                word_length = random.randint(1, 3)
                words.append(''.join(random.sample(alphabet, word_length)))
            clause = (' ' + action + ' ').join(words)
            if action == 'or':
                sentence = random.choice([item for item in words])

                def or_but_not_reward(answer, question=''):
                    correct = any(answer.find(word) >= 0 for word in words)
                    return correct, 1 if correct else -1
                question = 'say: ' + clause + '.'
                return question, or_but_not_reward, micro13_2_feedback
            else:
                sentence = ''.join(words)
                sentence += '.'
                question = 'say: ' + clause + '.'
                return question, [sentence], micro13_2_feedback

        return TaskGenerator(micro13_2_question, '', None, ';')


class Micro14Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro14_question(self):
            alphabet = string.ascii_lowercase
            idx = random.randint(0, len(alphabet) - 2)
            question = 'after {} comes what:.'.format(alphabet[idx])
            sentence = alphabet[idx + 1]
            sentence += '.'

            def micro14_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro14_feedback
        return TaskGenerator(micro14_question, '', None, ';')


class Micro15Task(MicroBase):
    reg_answer_end = r'\.'
    FAILED_TASK_TOLERANCE = 2.0

    @on_start()
    def new_task_instance(self, event):
        super(Micro15Task, self).new_task_instance(event)
        self.should_know = False

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro15Task, self).question_answered(is_correct)
        key = self.question.split()[-1].split('.')[0]
        self.mapping_check[key] = True
        if all(self.mapping_check.values()):
            self.should_know = True

    def get_task_generator(self):
        sequence1 = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
        sequence2 = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth']
        sequence3 = ['ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
        sequence4 = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
                     'sixteen', 'seventeen', 'eighteen', 'nineteen']

        chosen_sequence = random.choice([sequence1, sequence2, sequence3, sequence4])
        if random.randint(0, 2) > 0:
            chosen_sequence.reverse()

        self.mapping_check = {key: False for key in chosen_sequence[0:-1]}

        def micro15_question(self):
            def micro15_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            idx = random.randint(0, len(chosen_sequence) - 2)
            word = chosen_sequence[idx]
            question = 'say next after: ' + word + '.'
            sentence = chosen_sequence[idx + 1] + '.'
            return question, [sentence], micro15_feedback

        return TaskGenerator(micro15_question, '', None, ';')


class Micro16Task(MicroBase):
    reg_answer_end = r'\.'
    m8 = Micro9Sub2Task()
    m9 = Micro10Task()
    m10 = Micro11Task()
    m11 = Micro12Task()

    def get_task_generator(self):
        tasks = [self.m8, self.m9, self.m10, self.m11]
        task = random.choice(tasks)
        return task.get_task_generator()


class Micro19Task(MicroBase):
    reg_answer_end = r'\.'
    m10 = Micro10Task()
    m11 = Micro11Task()
    m12 = Micro12Task()
    m14 = Micro14Task()
    FAILED_TASK_TOLERANCE = 2.0
    synonyms = {'say': ['say', 'print', 'write'],
                'and': ['and', 'together with', '&', 'also'],
                'or': ['or', 'alternative', '/'],
                'after': ['after', 'behind', 'next'],
                'union': ['union', 'consolidate', 'joint'],
                'exclude': ['exclude', 'prohibit', 'ignore', 'remove']}

    tasks = []
    forbidden_strings = []
    for original, syn in synonyms.items():
        forbidden_strings.extend(syn)

    pattern_find = '(^|[^\w]){0}([^\w])'
    pattern_replace = '\g<1>{0}\g<2>'

    def replace(self, from_word, to_word, sentence):
        return re.sub(self.pattern_find.format(from_word), self.pattern_replace.format(to_word), sentence)

    @on_start()
    def new_task_instance(self, event):
        super(Micro19Task, self).new_task_instance(event)
        self.should_know = False

    def get_task_generator(self):
        # choose task randomly, but provide all n tasks in n tries
        if len(self.tasks) == 0:
            self.tasks = [self.m10, self.m11, self.m12, self.m14]
        task = random.choice(self.tasks)
        self.tasks.remove(task)
        task_generator = task.get_task_generator()
        func_inner = task_generator.instancer

        get_random_synonym = self.get_random_synonym

        def func_outer(self_):
            with forbid_dictionary_strings(self.forbidden_strings):
                question, a, b = func_inner(self_)

            for original in self.synonyms.keys():
                synonym = get_random_synonym(original)
                question = self.replace(original, synonym, question)
            return question, a, b
        task_generator.instancer = func_outer
        return task_generator

    def get_random_synonym(self, word):
        return random.choice(self.synonyms[word])


class Micro20Task(Micro19Task):
    tasks = []

    def get_task_generator(self):
        with forbid_dictionary_strings(self.forbidden_strings):
            content = load_dictionary(DICTIONARY_FILE)

        vocabulary = content[200:400]
        self.synonyms = {o: s for (o, s) in zip(self.synonyms.keys(), random.sample(vocabulary, len(self.synonyms)))}

        current_forbidden_strings = self.forbidden_strings + list(self.synonyms.values())

        # choose task randomly, but provide all n tasks in n tries
        if len(self.tasks) == 0:
            self.tasks = [self.m10, self.m11, self.m12, self.m14]
        task = random.choice(self.tasks)
        self.tasks.remove(task)

        task_generator = task.get_task_generator()
        func_inner = task_generator.instancer

        synonym_list = self.synonyms.keys()
        get_synonym = self.get_synonym

        def func_outer(self_):
            with forbid_dictionary_strings(current_forbidden_strings):
                question, a, b = func_inner(self_)

            synonym_present = [synonym for synonym in synonym_list if question.find(synonym) >= 0]
            synonym = random.choice(synonym_present)
            new_synonym = get_synonym(synonym)
            question = self.replace(synonym, new_synonym, question)
            question = new_synonym + " is as " + synonym + ' - ' + question
            return question, a, b
        task_generator.instancer = func_outer
        return task_generator

    def get_synonym(self, word):
        return self.synonyms[word]
