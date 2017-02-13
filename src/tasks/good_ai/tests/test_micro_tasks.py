import random
import string
import unittest
import re

from core.byte_channels import ByteInputChannel, ByteOutputChannel
from core.scheduler import ConsecutiveTaskScheduler
import core.environment as environment
import core.serializer as serializer
from learners.base import BaseLearner
from tasks.competition.tests.helpers import SingleTaskScheduler
import tasks.good_ai.micro as micro


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


class EnvironmentByteMessenger:

    def __init__(self, env, serializer):
        self._env = env
        self._serializer = serializer
        self._input_channel = ByteInputChannel(serializer)
        self._output_channel = ByteOutputChannel(serializer)
        self.init()

    def init(self):
        first_bit, reward = self._env.next(None)
        self._input_channel.consume(first_bit)
        self._input_channel.get_text()

    def send(self, msg=None):
        msg = msg or ' '
        nbits = 0
        self._output_channel.set_message(msg)
        while not self._output_channel.is_empty():
            env_bit, reward = self._env.next(self._output_channel.consume())
            self._input_channel.consume(env_bit)
            nbits += 1
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
        if reward < 0:
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
            self.answer = self.mapping[input][-1]
            self.is_feedback = not self.is_feedback
            return self.answer


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
            self.answer = self.mapping[self.last_input][-1]
            if input == '.':
                self.is_feedback = not self.is_feedback
                return self.answer


class TestMicro5Sub4Learner(BaseLearner):

    def __init__(self):
        self.awaiting_question = True
        self.awaiting_feedback = False
        self.question_separator = '.'
        self.feedback_separator = ';'
        self.mapping = {}
        self.question = None
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
        feedback = self.buffer[:-len(self.feedback_separator)]
        self.mapping[self.question] = ''.join(feedback)
        del self.buffer[:]
        self.awaiting_question = True
        self.awaiting_feedback = False

    def answer_question(self):
        print("answer on {} is {}".format(self.question, self.mapping.get(self.question, ' ')))
        return self.mapping.get(self.question, ' ')

    def next(self, input):
        self.buffer.append(input)

        if self.is_question:
            self.process_question()
            return self.answer_question()
        elif self.is_feedback:
            self.process_feedback()


class TestMicro6Sub1Learner(BaseLearner):

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


class TestMicro7Learner(TestMicro6Sub1Learner):

    def _handle_assignment(self, input):
        if len(self.buffer) >= 2 and self.buffer[-1] == ' ' and self.buffer[-2] == ' ':
            self.buffer.pop()  # trimming white spaces to a single one
        TestMicro6Sub1Learner._handle_assignment(self, input)


class TestMicro8Learner(TestMicro6Sub1Learner):

    def __init__(self):
        self.interleave_char = ' '
        TestMicro6Sub1Learner.__init__(self)

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

        commands = '|'.join(self._viable_commands)

        self._matcher = re.compile('(' + commands + '):(?: (\w*)|.)')

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


class TestMicro9Learner(TestMicroMultipleCommandsBase):
    _viable_commands = ['say']

    @classmethod
    def _generate_response(cls, commands):
        return ' '.join(command[1] for command in commands)


class TestMicro10Learner(TestMicroMultipleCommandsBase):
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


class TestMicro11Learner(TestMicroMultipleCommandsBase):
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


class TestMicro12Learner(BaseLearner):
    def __init__(self):
        self._buffer = []
        self._read_assignment = True
        self._output = []

        self._matcher = re.compile('after (.) comes what:')

    def next(self, input_char):
        self._buffer.append(input_char)

        if self._read_assignment:
            if input_char == '.':
                # Commands received.

                # Get the whole assignment, remove dot.
                received_sentence = ''.join(self._buffer)
                self._buffer = []

                char = self._matcher.findall(received_sentence)[0]

                idx = string.ascii_letters.find(char)
                response = string.ascii_letters[idx + 1]

                self._output = [response]

                self._read_assignment = False

        if not self._read_assignment:
            if len(self._output) > 0:
                return self._output.pop(0)
            else:
                self._read_assignment = True
                return '.'

        return ' '


def task_solved_successfuly(task):
    return task._env._last_result and task.solved_on_time()


def basic_task_run(messenger, learner, task):
    import sys
    while True:
        question = messenger.get_text()[-1]
        answer = learner.next(question)
        reward = messenger.send(answer)
        learner.reward(reward)
        if task._env._last_result is not None:    # agent succeeded
            break
        if not task.solved_on_time():   # agent is overtime
            messenger.send(' ')  # to force a switch of task and correct setting of _env._last_result
            break


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
        basic_task_run(self.messenger, learner, first_task)
        # I am still in the first task
        self.assertEqual(self.env._current_task, first_task)
        # and scheduler obtained one reward
        self.assertEqual(self.scheduler.reward_count, 1)

    def test_different_task_after_two_instances(self):
        self.perform_setup()
        first_task = self.env._current_task
        # first instance
        learner = TestMicro1Learner(first_task.alphabet)
        basic_task_run(self.messenger, learner, first_task)
        self.assertEqual(self.scheduler.reward_count, 1)
        # second instance
        learner = TestMicro1Learner(first_task.alphabet)
        consecutive_successes = first_task._env._task_scheduler.success_threshold
        for _ in range(consecutive_successes - 1):
            basic_task_run(self.messenger, learner, first_task)
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
        first_task.failed_task_tolerance = 0    # make the task really strict
        self.assertIsNotNone(first_task)
        learner = BaseLearner()
        self.env.task_updated.register(on_task_change)
        basic_task_run(self.messenger, learner, first_task)     # failure should be issued now
        self.messenger.send()   # now the task is overdue
        self.messenger.send()   # force the control loop to enter next task
        self.assertTrue(task_changed[0])
        self.assertEqual(self.env._current_task, first_task)
        self.assertEqual(self.scheduler.reward_count, 0)

# all tests in TestMicroTask should be also fulfilled by classes inheriting from TestMicroTaskBase at the bottom


class TestMicroTask(unittest.TestCase):

    def test_micro6_1_pass(self):
        # import logging  # useful to uncomment when you want to see logs during test runs
        # logging.basicConfig(level=logging.DEBUG)
        for _ in range(3):
            task = micro.Micro6Sub1Task()
            learner = TestMicro6Sub1Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_micro6_1_fail(self):
        for _ in range(3):
            task = micro.Micro6Sub1Task()
            learner = FixedLearner('.')
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertFalse(task_solved_successfuly(task))

    def test_micro6_2_pass(self):
        for _ in range(3):
            task = micro.Micro6Sub2Task()
            learner = TestMicro6Sub1Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_micro6_2_fail(self):
        for _ in range(3):
            task = micro.Micro6Sub2Task()
            learner = FixedLearner('.')
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertFalse(task_solved_successfuly(task))

    def test_micro6_3_pass(self):
        for _ in range(3):
            task = micro.Micro6Sub3Task()
            learner = TestMicro6Sub1Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_micro6_3_fail(self):
        for _ in range(3):
            task = micro.Micro6Sub3Task()
            learner = FixedLearner('.')
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertFalse(task_solved_successfuly(task))

    def test_micro7_pass(self):
        for _ in range(3):
            task = micro.Micro7Task()
            learner = TestMicro7Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_micro7_fail(self):
        for _ in range(3):
            task = micro.Micro7Task()
            learner = TestMicro6Sub1Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertFalse(task_solved_successfuly(task))

    def test_micro8_1_pass(self):
        for _ in range(3):
            task = micro.Micro8Sub1Task()
            learner = TestMicro8Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_micro8_1_fail(self):
        for _ in range(3):
            task = micro.Micro8Sub1Task()
            learner = TestMicro6Sub1Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertFalse(task_solved_successfuly(task))

    def test_micro8_2_pass(self):
        for _ in range(3):
            task = micro.Micro8Sub2Task()
            learner = TestMicro8Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_micro8_2_fail(self):
        for _ in range(3):
            task = micro.Micro8Sub2Task()
            learner = TestMicro6Sub1Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertFalse(task_solved_successfuly(task))

    def test_micro8_3_pass(self):
        for _ in range(3):
            task = micro.Micro8Sub3Task()
            learner = TestMicro8Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_micro8_3_fail(self):
        for _ in range(3):
            task = micro.Micro8Sub3Task()
            learner = TestMicro6Sub1Learner()
            messenger = task_messenger(task)
            for _ in range(3):
                basic_task_run(messenger, learner, task)
                self.assertFalse(task_solved_successfuly(task))


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
        task.success_tolerance = 0
        task.failed_task_tolerance = 0
        return task

    def _get_learner(self):
        pass

    def _get_failing_learner(self):
        return FixedLearner('*')

    def init_env(self, task, success_threshold=2):
        slzr = serializer.StandardSerializer()
        scheduler = ConsecutiveTaskScheduler([task], success_threshold)
        env = environment.Environment(slzr, scheduler, max_reward_per_task=float("inf"), byte_mode=True)
        messenger = EnvironmentByteMessenger(env, slzr)
        return (scheduler, messenger)

    def test_task(self):
        for _ in range(self.task_instance_multiplier):
            task = self._get_task()
            for _ in range(self.task_run_multiplier):
                learner = self._get_learner()
                messenger = task_messenger(task)
                basic_task_run(messenger, learner, task)
                self.assertTrue(task_solved_successfuly(task))

    def test_successful_evaluation(self):
        # Tests that task instance can be solved and that there are no residuals from 1st instance, which would prevent agent from solving 2nd instance
        task = self._get_task()
        scheduler, messenger = self.init_env(task)
        # first run
        learner = self._get_learner()
        basic_task_run(messenger, learner, task)
        self.assertTrue(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 1)

        # second run
        learner = self._get_learner()
        basic_task_run(messenger, learner, task)
        self.assertTrue(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 0)  # 2 % 2 = 0, because the scheduler switched to next task

    def test_failed_evaluation(self):
        # Tests that instance can be failed and that there are no residuals from 1st instance, which would solve the 2nd instance instead of agent
        task = self.task()
        scheduler, messenger = self.init_env(task)
        # first run
        learner = self._get_failing_learner()
        basic_task_run(messenger, learner, task)
        self.assertFalse(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 0)

        # second run
        basic_task_run(messenger, learner, task)
        self.assertFalse(task_solved_successfuly(task))
        self.assertEqual(scheduler.reward_count, 0)

    # this test fails - beacuse during the second run - env.last_result is already set to False from first run -> task run ends immediately
    # def test_failed_then_successful_evaluation(self):
    #     # Tests that instance can be failed and that there are no residuals from 1st instance, which would prevent agent from solving 2nd instance
    #     task = self._get_task()
    #     scheduler, messenger = self.init_env(task)
    #     # first run
    #     learner = self._get_failing_learner()
    #     basic_task_run(messenger, learner, task)
    #     self.assertFalse(task_solved_successfuly(task))
    #     self.assertEqual(scheduler.reward_count, 0)

    #     # second run
    #     learner = self._get_learner()
    #     basic_task_run(messenger, learner, task)
    #     self.assertTrue(task_solved_successfuly(task))
    #     self.assertEqual(scheduler.reward_count, 1)


class TestMicro1(TestMicroTaskBase):
    task = micro.Micro1Task

    def _get_learner(self):
        return TestMicro1Learner(string.ascii_letters + string.digits + ' ,.!;?-')


class TestMicro2(TestMicroTaskBase):
    task = micro.Micro2Task

    def _get_learner(self):
        return TestMicro1Learner(string.ascii_lowercase, True)


class TestMicro3(TestMicroTaskBase):
    task = micro.Micro3Task

    def _get_learner(self):
        return TestMicro3Learner()


class TestMicro4(TestMicroTaskBase):
    task = micro.Micro4Task

    def _get_learner(self):
        return BaseLearner()


class TestMicro5Sub1(TestMicroTaskBase):
    task = micro.Micro5Sub1Task

    def _get_learner(self):
        return TestMicro5Sub1Learner()


class TestMicro5Sub2(TestMicroTaskBase):
    task = micro.Micro5Sub2Task

    def _get_learner(self):
        return TestMicro5Sub2Learner()


class TestMicro5Sub3(TestMicroTaskBase):
    task = micro.Micro5Sub3Task

    def _get_learner(self):
        return TestMicro5Sub3Learner()


class TestMicro5Sub4(TestMicroTaskBase):
    task = micro.Micro5Sub4Task

    def _get_learner(self):
        return TestMicro5Sub4Learner()


class TestMicro6Sub1(TestMicroTaskBase):
    task = micro.Micro6Sub1Task

    def _get_learner(self):
        return TestMicro6Sub1Learner()


class TestMicro6Sub2(TestMicroTaskBase):
    task = micro.Micro6Sub2Task

    def _get_learner(self):
        return TestMicro6Sub1Learner()


class TestMicro6Sub3(TestMicroTaskBase):
    task = micro.Micro6Sub3Task

    def _get_learner(self):
        return TestMicro6Sub1Learner()


class TestMicro7(TestMicroTaskBase):
    task = micro.Micro7Task

    def _get_learner(self):
        return TestMicro7Learner()

    def _get_failing_learner(self):
        return TestMicro6Sub1Learner()


class TestMicro8Sub1(TestMicroTaskBase):
    task = micro.Micro8Sub1Task

    def _get_learner(self):
        return TestMicro8Learner()

    def _get_failing_learner(self):
        return TestMicro7Learner()


class TestMicro8Sub2(TestMicroTaskBase):
    task = micro.Micro8Sub2Task

    def _get_learner(self):
        return TestMicro8Learner()

    def _get_failing_learner(self):
        return TestMicro7Learner()


class TestMicro8Sub3(TestMicroTaskBase):
    task = micro.Micro8Sub3Task

    def _get_learner(self):
        return TestMicro8Learner()

    def _get_failing_learner(self):
        return TestMicro7Learner()


class TestMicro9(TestMicroTaskBase):
    task = micro.Micro9Task

    def _get_learner(self):
        return TestMicro9Learner()


class TestMicro10(TestMicroTaskBase):
    task = micro.Micro10Task

    def _get_learner(self):
        return TestMicro10Learner()


class TestMicro11(TestMicroTaskBase):
    task = micro.Micro11Task

    def _get_learner(self):
        return TestMicro11Learner()


class TestMicro12(TestMicroTaskBase):
    task = micro.Micro12Task

    def _get_learner(self):
        return TestMicro12Learner()


