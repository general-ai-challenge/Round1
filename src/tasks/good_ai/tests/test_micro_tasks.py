import string
import unittest

from core.byte_channels import ByteInputChannel, ByteOutputChannel
import core.environment as environment
import core.serializer as serializer
from learners.base import BaseLearner
from tasks.competition.tests.helpers import SingleTaskScheduler
import tasks.good_ai.micro as micro


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
        numbers = '0123456789'
        self.mapping = {x: list(numbers) for x in numbers}
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


class TestMicroTask(unittest.TestCase):

    def basic_run(self, messenger, learner, task):
        while True:
            question = messenger.get_text()[-1]
            answer = learner.next(question)
            reward = messenger.send(answer)
            learner.reward(reward)
            if task.agent_solved_instance() is not None:
                break

    def test_stupid_agent(self):
        task = micro.Micro1Task()
        learner = BaseLearner()
        messenger = task_messenger(task)
        self.basic_run(messenger, learner, task)
        self.assertFalse(task.agent_solved_instance())

    def test_micro1(self):
        for _ in range(10):
            task = micro.Micro1Task()
            learner = TestMicro1Learner(task.alphabet)
            messenger = task_messenger(task)
            self.basic_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance(), True)

    def test_micro2(self):
        for _ in range(10):
            learner = TestMicro1Learner(string.ascii_lowercase, True)
            task = micro.Micro2Task()
            messenger = task_messenger(task)
            self.basic_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance(), 0)

    def test_micro3(self):
        for _ in range(10):
            learner = TestMicro3Learner()
            task = micro.Micro3Task()
            messenger = task_messenger(task)
            self.basic_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance())

    def test_micro4(self):
        for _ in range(10):
            task = micro.Micro4Task()
            learner = BaseLearner()
            messenger = task_messenger(task)
            self.basic_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance())

    def test_micro5sub1(self):
        for _ in range(10):
            task = micro.Micro5Sub1Task()
            learner = TestMicro5Sub1Learner()
            messenger = task_messenger(task)
            self.basic_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance())
