# Copyright (c) 2017-present, GoodAI
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import random
import re
import string
import unittest

import core.environment as environment
import core.serializer as serializer
import tasks.challenge.round1.challenge_micro as micro
from core.byte_channels import ByteInputChannel, ByteOutputChannel
from core.scheduler import ConsecutiveTaskScheduler
from learners.base import BaseLearner
from tasks.competition.tests.helpers import SingleTaskScheduler


class FixedLearner:

    def __init__(self, fixed_output=' '):
        self.fixed_output = fixed_output
        return

    def try_reward(self, reward):
        if reward is not None:
            self.reward(reward)

    def reward(self, reward):
        # YEAH! Reward!!! Whatever...
        pass

    def next(self, input):
        # do super fancy computations
        # return our guess
        return self.fixed_output


class FaultingLearner(BaseLearner):

    def __init__(self, correct_learner, error_rate=0.1):
        self.correct_learner = correct_learner
        self.mistake_done = False
        self.dot_skipped = False
        self.error_rate = error_rate
        return

    def next(self, agents_input):
        if self.dot_skipped:
            self.mistake_done = False
            self.dot_skipped = False
            return '.'
        output = self.correct_learner.next(agents_input)
        if output == ' ':
            return ' '
        if output == '.':
            if self.mistake_done:
                self.mistake_done = False
                return '.'
            else:
                self.dot_skipped = True
                return random.choice(string.ascii_letters)
        if random.random() < self.error_rate:
            self.mistake_done = True
            return random.choice(string.ascii_letters)
        return output


class TextFaultingLearner(BaseLearner):

    def __init__(self, correct_learner):
        self._correct_learner = correct_learner
        self._make_mistake = False

    def next(self, input_char):
        if self._make_mistake:
            self._make_mistake = False
            return '.'

        response = self._correct_learner.next(input_char)
        if response is not None and response.endswith('.'):
            return response[:-1] + '4.'


class EnvironmentByteMessenger:

    def __init__(self, env, serializer):
        self._env = env
        self._serializer = serializer
        self._input_channel = ByteInputChannel(serializer)
        self._output_channel = ByteOutputChannel(serializer)
        self.init()

    def init(self):
        first_symbol, reward = self._env.next(None)
        self._input_channel.consume(first_symbol)
        self._input_channel.get_text()

    def send(self, msg=None):
        msg = msg or ' '
        nsymbols = 0
        self._output_channel.set_message(msg)
        while not self._output_channel.is_empty():
            env_symbol, reward = self._env.next(self._output_channel.consume())
            self._input_channel.consume(env_symbol)
            nsymbols += 1
        return reward

    def get_text(self):
        return self._input_channel.get_text()


def task_messenger(task):
    slzr = serializer.StandardSerializer()
    scheduler = SingleTaskScheduler(task)
    env = environment.Environment(slzr, scheduler, max_reward_per_task=float("inf"), byte_mode=True)
    return EnvironmentByteMessenger(env, slzr)


class TestMicro1Learner(BaseLearner):

    def __init__(self, alphabet, preserve_specials=False):
        self.valid_chars = list(alphabet)
        self.char = None
        self.preserve_specials = preserve_specials

    def next(self, input):
        if self.preserve_specials and input not in string.ascii_lowercase:
            return input
        if not self.char:
            self.char = self.valid_chars.pop()
        return self.char

    def reward(self, reward):
        if reward < 0 and len(self.valid_chars) > 0:
            self.char = None


class TestMicro3Learner(BaseLearner):

    def __init__(self):
        self.mapping = {x: list(string.ascii_lowercase) for x in string.ascii_lowercase}

    def next(self, input):
        self.last_input = input
        if input not in string.ascii_lowercase:
            self.answer = input
        else:
            possible_values = self.mapping[input]
            self.answer = possible_values[-1]
        return self.answer

    def reward(self, reward):
        if reward < 0:
            self.mapping[self.last_input].pop()
        else:
            for options in self.mapping.values():
                if self.answer in options:
                    options.remove(self.answer)
            self.mapping[self.last_input] = [self.answer]


class TestMicro5Sub1Learner(BaseLearner):

    def __init__(self):
        self.mapping = {x: list(string.digits) for x in string.digits}
        self.is_feedback = False

    def next(self, input):
        if self.is_feedback:
            self.mapping[self.last_input] = [input]
            self.is_feedback = not self.is_feedback
            return
        else:
            self.last_input = input
            if input in self.mapping:   # for usage with other than 5.1 task
                self.answer = self.mapping[input][-1]
            self.is_feedback = not self.is_feedback
            return self.answer

    def try_reward(self, reward):
        if reward is None:
            assert False


class TestMicro5Sub2Learner(BaseLearner):

    def __init__(self):
        self.mapping = {x: list(string.digits) for x in string.digits}
        self.is_feedback = False

    def next(self, input):
        if input == ';':
            return
        if self.is_feedback:
            self.mapping[self.last_input] = [input]
            self.is_feedback = not self.is_feedback
            return
        else:
            self.last_input = input
            if input in self.mapping:   # for usage with other than 5.1 task
                self.answer = self.mapping[input][-1]
            self.is_feedback = not self.is_feedback
            return self.answer


class TestMicro5Sub3Learner(BaseLearner):

    def __init__(self):
        self.mapping = {x: list(string.digits) for x in string.digits}
        self.is_feedback = False

    def next(self, input):
        if input == ';':
            return
        if self.is_feedback:
            self.mapping[self.last_input] = [input]
            self.is_feedback = not self.is_feedback
        else:
            if input != '.':
                self.last_input = input
            if self.last_input in self.mapping:   # for usage with other than 5.3 task
                self.answer = self.mapping[self.last_input][-1]
            if input == '.':
                self.is_feedback = not self.is_feedback
                return self.answer


class TestMicroQuestionAnswerBase(BaseLearner):

    def __init__(self):
        self.awaiting_question = True
        self.awaiting_feedback = False
        self.question_separator = '.'
        self.feedback_separator = ';'
        self.question = None
        self.feedback = None
        self.buffer = []

    @property
    def is_question(self):
        return self.awaiting_question and self.buffer[-1] == self.question_separator

    @property
    def is_feedback(self):
        return self.awaiting_feedback and self.buffer[-1] == self.feedback_separator

    def process_question(self):
        self.question = ''.join(self.buffer[:-len(self.question_separator)])
        del self.buffer[:]
        self.awaiting_question = False
        self.awaiting_feedback = True

    def process_feedback(self):
        self.feedback = self.buffer[:-len(self.feedback_separator)]
        del self.buffer[:]
        self.awaiting_question = True
        self.awaiting_feedback = False

    def answer_question(self):
        pass

    def answer_feedback(self):
        pass

    def next(self, input):
        self.buffer.append(input)
        if self.is_question:
            self.process_question()
            return self.answer_question()
        elif self.is_feedback:
            self.process_feedback()
            return self.answer_feedback()


class TestMicro5Sub4Learner(TestMicroQuestionAnswerBase):

    def __init__(self):
        super(TestMicro5Sub4Learner, self).__init__()
        self.mapping = {}

    def answer_feedback(self):
        self.mapping[self.question] = ''.join(self.feedback)

    def answer_question(self):
        return self.mapping.get(self.question, '.')

    def reward(self, reward):
        if reward and reward != 0:
            del self.buffer[:]


class TestMicro5Sub6Learner(TestMicro5Sub4Learner):

    def answer_feedback(self):
        feedback = self.feedback
        if feedback[-1] == '.':
            feedback = feedback[:-1]
        self.mapping[self.question] = ''.join(feedback)

    def answer_question(self):
        if self.question in self.mapping:
            return self.mapping[self.question] + '.'
        else:
            return '.'


class TestMicro5Sub10Learner(TestMicro5Sub4Learner):

    def answer_feedback(self):
        desired_len = 2
        feedback = self.feedback[-desired_len:]

        self.mapping[self.question] = ''.join(feedback)
        del self.buffer[:]
        self.awaiting_question = True
        self.awaiting_feedback = False


class TestMatchQuestionAndFeedbackBase(BaseLearner):
    matcher_feedback = None
    matcher_output = None

    def __init__(self):
        self._buffer = []
        self._read_assignment = True
        self._output = []

    def next(self, input_char):
        self._buffer.append(input_char)

        if self._read_assignment:
            if input_char == '.':
                # Commands received.

                # Get the whole assignment, remove dot.
                received_sentence = ''.join(self._buffer)

                if self.matcher_feedback is None:
                    feedback_match = ['']
                else:
                    feedback_match = self.matcher_feedback.findall(received_sentence)
                output_match = self.matcher_output.findall(received_sentence)
                if len(output_match) > 0:
                    self._output = list(self.generate_response(feedback_match, output_match))
                    self._buffer = []
                    self._read_assignment = False

        if not self._read_assignment:
            if len(self._output) > 0:
                return self._output.pop(0)
            else:
                self._read_assignment = True
                return '.'

        return ' '

    def generate_response(self, feedback_match, output_match):
        raise NotImplementedError()


class TestMicro6Learner(TestMatchQuestionAndFeedbackBase):
    matcher_feedback = re.compile('! (.+)\. ?;')
    matcher_output = re.compile('random_map: (.+)\.')

    def __init__(self):
        super(TestMicro6Learner, self).__init__()
        self.previous_symbol = ''
        self.mapping = {}

    def generate_response(self, feedback_match, output_match):
        output = output_match[0]
        if len(feedback_match) > 0:
            feedback = feedback_match[0]
            self.mapping[self.previous_symbol] = feedback

        self.previous_symbol = output
        if output in self.mapping.keys():
            return self.mapping[output]
        else:
            return ' '


class TestMicro7Sub1Learner(BaseLearner):

    def __init__(self):
        self.buffer = []
        self.mapping = {}
        self.is_feedback = False
        self.is_output = False
        self.is_assignment = True
        self.assignment = []
        self.response_buffer = []

    def _handle_feedback(self, input):
        if input != ';':
            return ' '
        self.buffer.pop()  # remove the ';'
        dot_index = self.buffer.index('.')
        self.mapping[str(self.assignment)] = self.buffer[dot_index + 2:]  # +2 to remove the dot and the ensuing space
        del self.buffer[:]  # same as self.buffer.clear() in python 3.5
        self.is_feedback = False
        self.is_assignment = True
        return ' '

    def _handle_assignment(self, input):
        if input == '.':
            colon_index = self.buffer.index(':')
            self.assignment = self.buffer[colon_index + 2:]  # +2 to remove the colon and the ensuing space

            self.assignment.reverse()
            self.is_output = True
            self.is_assignment = False

    def _handle_output(self, input):
        self.answer = self.assignment.pop()
        if self.answer == '.':
            self.is_output = False
            self.is_feedback = True
        return self.answer

    def next(self, input):
        self.buffer.append(input)

        if self.is_feedback:
            return self._handle_feedback(input)

        if self.is_assignment:
            self._handle_assignment(input)
            # the return is intentionally missing here - because of the need to immediately switch from
            # assignment to output when the '.' character is read.

        if self.is_output:
            return self._handle_output(input)

        return ' '


class TestMicro8Learner(TestMicro7Sub1Learner):

    def _handle_assignment(self, input):
        if len(self.buffer) >= 2 and self.buffer[-1] == ' ' and self.buffer[-2] == ' ':
            self.buffer.pop()  # trimming white spaces to a single one
        TestMicro7Sub1Learner._handle_assignment(self, input)


class TestMicro9Learner(TestMicro7Sub1Learner):

    def __init__(self):
        self.interleave_char = ' '
        TestMicro7Sub1Learner.__init__(self)

    def _handle_assignment(self, input):
        if len(self.buffer) >= 2 and self.buffer[-1] == ' ' and self.buffer[-2] == ' ':
            self.buffer.pop()  # trimming white spaces to a single one
        if input == '.':

            remove_last_interleave_char = False

            colon_index = self.buffer.index(':')
            self.assignment = self.buffer[colon_index + 2:]  # +2 to remove the colon and the ensuing space
            if len(self.assignment) > 5 and "".join(self.assignment[-6:-2]) == " by ":  # to handle interleave: abc by -.
                self.interleave_char = self.assignment[-2]
                self.assignment = self.assignment[0:-6]
                remove_last_interleave_char = True
            else:
                self.interleave_char = ' '
                self.assignment.pop()  # remove the trailing period

            # add the interleave character to the string which will be output
            assignment_len = len(self.assignment)
            for index in reversed(range(assignment_len)):
                self.assignment.insert(index + 1, self.interleave_char)

            if remove_last_interleave_char:
                self.assignment.pop()

            self.assignment.append('.')

            self.assignment.reverse()
            self.is_output = True
            self.is_assignment = False


class TestMicroMultipleCommandsBase(BaseLearner):
    _viable_commands = []

    def __init__(self):
        self._buffer = []
        self._read_assignment = True
        self._output = []

        commands = '|'.join(self._viable_commands)

        self._matcher = re.compile('(' + commands + '):(?: ([\w\-]*)|.)')

    @classmethod
    def _generate_response(cls, commands):
        raise NotImplementedError()

    def next(self, input_char):
        self._buffer.append(input_char)

        if self._read_assignment:
            if input_char == '.':
                # Commands received.

                # Get the whole assignment, remove dot.
                received_sentence = ''.join(self._buffer)
                self._buffer = []

                # Get a list of pairs: [(command, argument), ...], argument can be ''.
                commands = self._matcher.findall(received_sentence)

                if len(commands) == 0:
                    return ' '

                response = self._generate_response(commands)
                self._output = [c for c in response]

                self._read_assignment = False

        if not self._read_assignment:
            if len(self._output) > 0:
                return self._output.pop(0)
            else:
                self._read_assignment = True
                return '.'

        return ' '


class TestMicro10Learner(TestMicroMultipleCommandsBase):
    _viable_commands = ['say']

    @classmethod
    def _generate_response(cls, commands):
        return ' '.join(command[1] for command in commands)


class TestMicro11Learner(TestMicroMultipleCommandsBase):
    _viable_commands = ['say', 'reverse', 'concatenate', 'interleave']

    @classmethod
    def _generate_response(cls, commands):
        words = [command[1] for command in commands[:-1]]
        operation = commands[-1][0]

        if operation == 'reverse':
            return ' '.join(reversed(words))
        elif operation == 'concatenate':
            return ''.join(words)
        elif operation == 'interleave':
            return ''.join((''.join(word) for word in zip(*words)))
        else:
            raise ValueError('Wrong question: ' + str(commands))


class TestMicro12Learner(TestMicroMultipleCommandsBase):
    _viable_commands = ['say', 'union', 'exclude']

    @classmethod
    def _generate_response(cls, commands):
        words = [command[1] for command in commands[:-1]]
        operation = commands[-1][0]

        set1 = words[0]
        set2 = words[1]

        if operation == 'union':
            if set1.find(set2) >= 0:
                return set1
            else:
                return set1 + set2
        elif operation == 'exclude':
            return set1.replace(set2, '')


class TestMicro13Learner(TestMicro5Sub4Learner):

    def __init__(self, failing=False):
        super(TestMicro13Learner, self).__init__()
        self._failing = failing

    def answer_question(self):
        words = self.question.strip().split(' ')
        command, words = words[0], words[1:]

        if command == 'say:':
            result = ' '
            if words[1] == 'and' and words[2] != 'not':
                result = ''.join(words[::2])
                if self._failing:
                    result += '2'
            elif words[1] == 'or':
                if len(words) > 3 and words[3] == 'but' and words[4] == 'not':
                    result = words[0] if words[0] != words[5] else words[2]
                else:
                    result = words[0]

                if self._failing:
                    result += '2'
            elif words[0] == 'anything':
                result = 'a' if 'a' != words[3] else 'b'
                if self._failing:
                    result = words[3]

            return result + '.'
        else:
            return ' '


class TestMicro14Learner(TestMatchQuestionAndFeedbackBase):
    matcher_output = re.compile('after (.) comes what:')

    def generate_response(self, feedback_match, output_match):
        idx = string.ascii_letters.find(output_match[0])
        response = string.ascii_letters[idx + 1]
        return response


class TestMicro15Learner(TestMatchQuestionAndFeedbackBase):
    matcher_feedback = re.compile('! (.+)\. ?;')
    matcher_output = re.compile('say next after: (.+)\.')

    def __init__(self):
        super(TestMicro15Learner, self).__init__()
        self.previous_symbol = ''
        self.mapping = {}

    def generate_response(self, feedback_match, output_match):
        output = output_match[0]
        if len(feedback_match) > 0:
            feedback = feedback_match[0]
            self.mapping[self.previous_symbol] = feedback

        self.previous_symbol = output
        if output in self.mapping.keys():
            return self.mapping[output]
        else:
            return ' '


class TestMicroQuestionAnswerDelegatingBase(TestMicroQuestionAnswerBase):

    def delegate(self, learner, question):
        # Feed the learner the question.
        for c in question:
            learner.next(c)

        # Get response back from learner.
        response = learner.next('.')
        if len(response) > 1:
            return response

        response = [response]

        while response[-1] != '.':
            response.append(learner.next(' '))

        return ''.join(response)


class TestMicro16Learner(TestMicroQuestionAnswerDelegatingBase):

    def answer_question(self):
        # Depending on the question, choose a learner.
        if 'spell:' in self.question:
            learner = TestMicro9Learner()
        elif 'reverse:' in self.question or 'concatenate' in self.question or 'interleave' in self.question:
            learner = TestMicro11Learner()
        elif 'union:' in self.question or 'exclude' in self.question:
            learner = TestMicro12Learner()
        elif 'say:' in self.question:
            learner = TestMicro10Learner()
        else:
            learner = None

        if learner is None:
            return ' '

        return self.delegate(learner, self.question)


class TestMicro19Learner(TestMicroQuestionAnswerDelegatingBase):
    synonyms = {'say': ['say', 'print', 'write'],
                'and': ['and', 'together with', '&', 'also'],
                'or': ['or', 'alternative', '/'],
                'after': ['after', 'behind', 'next'],
                'union': ['union', 'consolidate', 'joint'],
                'exclude': ['exclude', 'prohibit', 'ignore', 'remove']}

    pattern_find = '(^|[^\w]){0}([^\w])'
    pattern_replace = '\g<1>{0}\g<2>'

    def replace(self, from_word, to_word, sentence):
        return re.sub(self.pattern_find.format(from_word), self.pattern_replace.format(to_word), sentence)

    def answer_question(self):
        for synonym in self.synonyms['say']:
            self.question = self.replace(synonym, 'say', self.question)

        learner = None

        if self.question.find('what:') >= 0:
            for synonym in self.synonyms['after']:
                self.question = self.replace(synonym, 'after', self.question)
            learner = TestMicro14Learner()

        if learner is None and ('concatenate:' in self.question or 'reverse:' in self.question or 'interleave:' in self.question):
            learner = TestMicro11Learner()

        if learner is None:
            is_learner_11 = False
            for synonym in self.synonyms['union']:
                if synonym in self.question:
                    self.question = self.replace(synonym, 'union', self.question)
                    learner = TestMicro12Learner()
                    is_learner_11 = True
            for synonym in self.synonyms['exclude']:
                if synonym in self.question:
                    self.question = self.replace(synonym, 'exclude', self.question)
                    learner = TestMicro12Learner()
                    is_learner_11 = True
            if is_learner_11:
                for synonym in self.synonyms['and']:
                    self.question = self.replace(synonym, 'and', self.question)
                for synonym in self.synonyms['or']:
                    self.question = self.replace(synonym, 'or', self.question)

        if learner is None:
            if 'say:' in self.question:
                learner = TestMicro10Learner()
            else:
                raise ValueError('Learner not found')

        return self.delegate(learner, self.question)


class TestMicro20Learner(TestMicroQuestionAnswerDelegatingBase):

    def __init__(self):
        super(TestMicro20Learner, self).__init__()
        self._matcher = re.compile('([^ ]+) is as ([^ ]+) - (.*)')

    def answer_question(self):
        to_word, from_word, rest = self._matcher.findall(self.question)[0]

        learner = TestMicro19Learner()
        for key in list(learner.synonyms.keys()):
            learner.synonyms[key] = [key]
        learner.synonyms[from_word] = [to_word]

        return self.delegate(learner, rest)


def task_solved_successfully(task):
    return task._env._last_result and task.under_time_limit_for_successfull_solution()


def basic_task_run(test, messenger, learner, task):
    limit = task._max_time
    temp_max_questions_nr = None
    while True:
        limit -= 1
        if limit < 1:
            test.assertFalse(True)  # raise the timeout constant on these tasks, because they are not finishing
            # on nr_of_questions timeout, but on nr_of_characters timeout
            break
        question = messenger.get_text()[-1]
        answer = learner.next(question)
        reward = messenger.send(answer)
        learner.reward(reward)
        if task._env._last_result is not None:    # agent succeeded
            if temp_max_questions_nr is not None:
                task.max_questions_nr = None  # not strictly necessary, but is here for clarity.
                temp_max_questions_nr = None
            break
        if not task.under_time_limit_for_successfull_solution():   # agent is overtime
            # follows a hack to make sure the agent will timeout inside the check_if_task_instance_finished method
            if temp_max_questions_nr is None:
                temp_max_questions_nr = task.max_questions_nr
            task.max_questions_nr = 1


class TestMicroTaskFlow(unittest.TestCase):

    def perform_setup(self, success_threshold=2):
        slzr = serializer.StandardSerializer()
        self.tasks = [micro.Micro1Task(), micro.Micro2Task(), micro.Micro3Task(), micro.Micro4Task(), micro.Micro5Sub1Task()]
        self.scheduler = ConsecutiveTaskScheduler(self.tasks, success_threshold)
        self.env = environment.Environment(slzr, self.scheduler, max_reward_per_task=float("inf"), byte_mode=True)
        self.messenger = EnvironmentByteMessenger(self.env, slzr)

    def test_same_task_after_solving_first_instance(self):
        self.perform_setup()
        first_task = self.env._current_task
        self.assertIsNotNone(first_task)
        learner = TestMicro1Learner(first_task.alphabet)
        basic_task_run(self, self.messenger, learner, first_task)
        # I am still in the first task
        self.assertEqual(self.env._current_task, first_task)
        # and scheduler obtained one reward
        self.assertEqual(self.scheduler.reward_count, 1)

    def test_different_task_after_two_instances(self):
        self.perform_setup()
        first_task = self.env._current_task
        # first instance
        learner = TestMicro1Learner(first_task.alphabet)
        basic_task_run(self, self.messenger, learner, first_task)
        self.assertEqual(self.scheduler.reward_count, 1)
        # second instance
        learner = TestMicro1Learner(first_task.alphabet)
        consecutive_successes = first_task._env._task_scheduler.success_threshold
        for _ in range(consecutive_successes - 1):
            basic_task_run(self, self.messenger, learner, first_task)
        # I should have 0 rewards now, because I switched to next task
        self.assertEqual(self.scheduler.reward_count, 0)
        self.messenger.send()  # force the control loop to enter next task
        self.assertNotEqual(self.env._current_task, first_task)
        # scheduler moved onto the next task
        self.assertEqual(self.env._current_task, self.tasks[1])
        # scheduler restarted the reward counter
        self.assertEqual(self.scheduler.reward_count, 0)

    def test_task_instance_change_for_stupid_agent(self):
        self.perform_setup(1)
        task_changed = [False]  # use list, which I can mutate from within the closure

        def on_task_change(*args):
            task_changed[0] = True
        first_task = self.env._current_task
        first_task.FAILED_TASK_TOLERANCE = 0    # make the task really strict
        self.assertIsNotNone(first_task)
        learner = BaseLearner()
        self.env.task_updated.register(on_task_change)
        basic_task_run(self, self.messenger, learner, first_task)     # failure should be issued now
        self.messenger.send()   # now the task is overdue
        self.messenger.send()   # force the control loop to enter next task
        self.assertTrue(task_changed[0])
        self.assertEqual(self.env._current_task, first_task)
        self.assertEqual(self.scheduler.reward_count, 0)


def init_env(task, success_threshold=2):
    slzr = serializer.StandardSerializer()
    scheduler = ConsecutiveTaskScheduler([task], success_threshold)
    env = environment.Environment(slzr, scheduler, max_reward_per_task=float("inf"), byte_mode=True)
    messenger = EnvironmentByteMessenger(env, slzr)
    return (scheduler, messenger)


class TestMicroTaskReward(unittest.TestCase):

    def test_valid_reward_on_newline(self):
        scheduler, messenger = init_env(micro.Micro1Task())
        learner = FixedLearner('\n')
        question = messenger.get_text()[-1]
        answer = learner.next(question)
        reward = messenger.send(answer)
        self.assertIsNotNone(reward)


class TestMicroTaskBase(unittest.TestCase):

    task = None
    task_instance_multiplier = 3
    task_run_multiplier = 10

    @classmethod
    def setUpClass(cls):
        if cls is TestMicroTaskBase:
            raise unittest.SkipTest("Skip MicroTaskBase tests, it's a base class")
        super(TestMicroTaskBase, cls).setUpClass()

    def _get_task(self):
        task = self.task()
        task.SUCCESS_TOLERANCE = 0
        task.FAILED_TASK_TOLERANCE = 0
        return task

    def _get_learner(self):
        pass

    def _get_failing_learner(self):
        return FixedLearner('*')

    def test_task(self):
        for _ in range(self.task_instance_multiplier):
            task = self._get_task()
            for _ in range(self.task_run_multiplier):
                learner = self._get_learner()
                messenger = task_messenger(task)
                basic_task_run(self, messenger, learner, task)
                self.assertTrue(task_solved_successfully(task))

    def test_successful_evaluation(self):
        # Tests that task instance can be solved and that there are no residuals from 1st instance, which would prevent agent from solving 2nd instance
        task = self._get_task()
        scheduler, messenger = init_env(task)
        # first run
        learner = self._get_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertTrue(task_solved_successfully(task))
        self.assertEqual(scheduler.reward_count, 1)

        # second run
        learner = self._get_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertTrue(task_solved_successfully(task))
        self.assertEqual(scheduler.reward_count, 0)  # 2 % 2 = 0, because the scheduler switched to next task

    def test_failed_evaluation(self):
        # Tests that instance can be failed and that there are no residuals from 1st instance, which would solve the 2nd instance instead of agent
        task = self._get_task()
        scheduler, messenger = init_env(task)
        # first run
        learner = self._get_failing_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertFalse(task_solved_successfully(task))
        self.assertEqual(scheduler.reward_count, 0)

        # second run
        basic_task_run(self, messenger, learner, task)
        self.assertFalse(task_solved_successfully(task))
        self.assertEqual(scheduler.reward_count, 0)

    def test_failed_then_successful_evaluation(self):
        # Tests that instance can be failed and that there are no residuals from 1st instance, which would prevent agent from solving 2nd instance

        task = self._get_task()
        scheduler, messenger = init_env(task)
        # first run
        learner = self._get_failing_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertFalse(task_solved_successfully(task))
        self.assertEqual(scheduler.reward_count, 0)

        # second run
        learner = self._get_learner()
        basic_task_run(self, messenger, learner, task)
        self.assertTrue(task_solved_successfully(task))
        self.assertEqual(scheduler.reward_count, 1)


class TestMicro1(TestMicroTaskBase):
    task = micro.Micro1Task

    def _get_learner(self):
        return TestMicro1Learner(string.ascii_letters + string.digits + ' ,.!;?-')

    def _get_failing_learner(self):
        return BaseLearner()


class TestMicro2(TestMicroTaskBase):
    task = micro.Micro2Task

    def _get_learner(self):
        return TestMicro1Learner(string.ascii_lowercase, True)


class TestMicro3(TestMicroTaskBase):
    task = micro.Micro3Task

    def _get_learner(self):
        return TestMicro3Learner()

    def _get_failing_learner(self):
        return TestMicro1Learner(string.ascii_lowercase)


class TestMicro4(TestMicroTaskBase):
    task = micro.Micro4Task

    def _get_learner(self):
        return BaseLearner()

    def _get_failing_learner(self):
        return TestMicro1Learner(string.ascii_lowercase)


class TestMicro5Sub1(TestMicroTaskBase):
    task = micro.Micro5Sub1Task

    def _get_learner(self):
        return TestMicro5Sub1Learner()

    def _get_failing_learner(self):
        return TestMicro1Learner(string.digits)


class TestMicro5Sub2(TestMicroTaskBase):
    task = micro.Micro5Sub2Task

    def _get_learner(self):
        return TestMicro5Sub2Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub1Learner()


class TestMicro5Sub3(TestMicroTaskBase):
    task = micro.Micro5Sub3Task

    def _get_learner(self):
        return TestMicro5Sub3Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub4(TestMicroTaskBase):
    task = micro.Micro5Sub4Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub5(TestMicroTaskBase):
    task = micro.Micro5Sub5Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub6(TestMicroTaskBase):
    task = micro.Micro5Sub6Task

    def _get_learner(self):
        return TestMicro5Sub6Learner()


class TestMicro5Sub7(TestMicroTaskBase):
    task = micro.Micro5Sub7Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub8(TestMicroTaskBase):
    task = micro.Micro5Sub8Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub9(TestMicroTaskBase):
    task = micro.Micro5Sub9Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub10(TestMicroTaskBase):
    task = micro.Micro5Sub10Task

    def _get_learner(self):
        return TestMicro5Sub10Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub4Learner()


class TestMicro5Sub11(TestMicroTaskBase):
    task = micro.Micro5Sub11Task

    def _get_learner(self):
        return TestMicro5Sub10Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub4Learner()


class TestMicro5Sub12(TestMicroTaskBase):
    task = micro.Micro5Sub12Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub13(TestMicroTaskBase):
    task = micro.Micro5Sub13Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub14(TestMicroTaskBase):
    task = micro.Micro5Sub14Task

    def _get_learner(self):
        return TestMicro5Sub10Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub4Learner()


class TestMicro5Sub15(TestMicroTaskBase):
    task = micro.Micro5Sub15Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub16(TestMicroTaskBase):
    task = micro.Micro5Sub16Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub17(TestMicroTaskBase):
    task = micro.Micro5Sub17Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub18(TestMicroTaskBase):
    task = micro.Micro5Sub18Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()

    def _get_failing_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro6(TestMicroTaskBase):
    task = micro.Micro6Task

    def _get_learner(self):
        return TestMicro6Learner()

    def _get_failing_learner(self):
        return FaultingLearner(TestMicro6Learner(), 0.3)


class TestMicro7Sub1(TestMicroTaskBase):
    task = micro.Micro7Sub1Task

    def _get_learner(self):
        return TestMicro7Sub1Learner()

    def _get_failing_learner(self):
        return FixedLearner('.')


class TestMicro7Sub2(TestMicroTaskBase):
    task = micro.Micro7Sub2Task

    def _get_learner(self):
        return TestMicro7Sub1Learner()

    def _get_failing_learner(self):
        return FixedLearner('.')


class TestMicro7Sub3(TestMicroTaskBase):
    task = micro.Micro7Sub3Task

    def _get_learner(self):
        return TestMicro7Sub1Learner()

    def _get_failing_learner(self):
        return FixedLearner('.')


class TestMicro8(TestMicroTaskBase):
    task = micro.Micro8Task

    def _get_learner(self):
        return TestMicro8Learner()

    def _get_failing_learner(self):
        return TestMicro7Sub1Learner()


class TestMicro9Sub1(TestMicroTaskBase):
    task = micro.Micro9Sub1Task

    def _get_learner(self):
        return TestMicro9Learner()

    def _get_failing_learner(self):
        return TestMicro8Learner()


class TestMicro9Sub2(TestMicroTaskBase):
    task = micro.Micro9Sub2Task

    def _get_learner(self):
        return TestMicro9Learner()

    def _get_failing_learner(self):
        return TestMicro8Learner()


class TestMicro9Sub3(TestMicroTaskBase):
    task = micro.Micro9Sub3Task

    def _get_learner(self):
        return TestMicro9Learner()

    def _get_failing_learner(self):
        return TestMicro8Learner()


class TestMicro10(TestMicroTaskBase):
    task = micro.Micro10Task

    def _get_learner(self):
        return TestMicro10Learner()

    def _get_failing_learner(self):
        return TextFaultingLearner(TestMicro10Learner())


class TestMicro11(TestMicroTaskBase):
    task = micro.Micro11Task

    def _get_learner(self):
        return TestMicro11Learner()

    def _get_failing_learner(self):
        return TextFaultingLearner(TestMicro11Learner())


class TestMicro12(TestMicroTaskBase):
    task = micro.Micro12Task

    def _get_learner(self):
        return TestMicro12Learner()

    def _get_failing_learner(self):
        return TextFaultingLearner(TestMicro12Learner())


class TestMicro13Sub1(TestMicroTaskBase):
    task = micro.Micro13Sub1Task

    def _get_learner(self):
        return TestMicro13Learner()

    def _get_failing_learner(self):
        return TestMicro13Learner(failing=True)


class TestMicro13Sub2(TestMicroTaskBase):
    task = micro.Micro13Sub2Task

    def _get_learner(self):
        return TestMicro13Learner()

    def _get_failing_learner(self):
        return TestMicro13Learner(failing=True)


class TestMicro14(TestMicroTaskBase):
    task = micro.Micro14Task

    def _get_learner(self):
        return TestMicro14Learner()

    def _get_failing_learner(self):
        return FaultingLearner(TestMicro14Learner(), 0.7)


class TestMicro15(TestMicroTaskBase):
    task = micro.Micro15Task

    def _get_learner(self):
        return TestMicro15Learner()

    def _get_failing_learner(self):
        return FaultingLearner(TestMicro15Learner(), 0.3)


class TestMicro16(TestMicroTaskBase):
    task = micro.Micro16Task

    def _get_learner(self):
        return TestMicro16Learner()

    def _get_failing_learner(self):
        return TextFaultingLearner(TestMicro16Learner())


class TestMicro19(TestMicroTaskBase):
    task = micro.Micro19Task

    def _get_learner(self):
        return TestMicro19Learner()

    def _get_failing_learner(self):
        return TextFaultingLearner(TestMicro19Learner())


class TestMicro20(TestMicroTaskBase):
    task = micro.Micro20Task

    def _get_learner(self):
        return TestMicro20Learner()

    def _get_failing_learner(self):
        return TextFaultingLearner(TestMicro20Learner())
