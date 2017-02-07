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
        self.cum_reward = 0
        self.init()

    def init(self):
        first_bit, reward = self._env.next(None)
        self._input_channel.consume(first_bit)
        self._input_channel.get_text()

    def send(self, msg=None):
        if msg is None:
            msg = self._serializer.SILENCE_TOKEN
        nbits = 0
        self._output_channel.set_message(msg)
        while not self._output_channel.is_empty():
            env_bit, reward = self._env.next(self._output_channel.consume())
            self._input_channel.consume(env_bit)
            if reward is not None:
                self.cum_reward += reward
            nbits += 1
        return reward

    def get_text(self):
        return self._input_channel.get_text()

    def get_cumulative_reward(self):
        return self.cum_reward


def task_messenger(task_funct):
    slzr = serializer.StandardSerializer()
    task = task_funct()
    scheduler = SingleTaskScheduler(task)
    env = environment.Environment(slzr, scheduler, max_reward_per_task=float("inf"), byte_mode=True)
    return EnvironmentByteMessenger(env, slzr)


class TestMicro1Learner(BaseLearner):
    pass


class TestMicro2Learner(BaseLearner):

    def __init__(self):
        self.valid_chars = list(string.ascii_lowercase)
        self.char = None

    def next(self, input):
        if input not in string.ascii_lowercase:
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


class TestMicroTask(unittest.TestCase):

    def basic_run(self, messenger, learner, rounds=10):
        for _ in range(rounds):
            question = messenger.get_text()[-1]
            # print("question read {}".format(repr(question)))
            answer = learner.next(question)
            # print("answer read {}".format(repr(answer)))
            reward = messenger.send(answer)
            # print("rward obtained {}".format(reward))
            # cum_reward = messenger.get_cumulative_reward()
            # print("cumulative reward read {}".format(cum_reward))
            learner.reward(reward)

    def test_micro1(self):
        for _ in range(10):
            learner = TestMicro1Learner()
            expected_reward = 0
            messenger = task_messenger(micro.Micro1Task)
            for _ in range(10):
                question = messenger.get_text()[-1]
                if question != " ":
                    expected_reward += 1
                answer = learner.next(question)
                reward = messenger.send(answer)
                learner.reward(reward)
            self.assertEqual(messenger.get_cumulative_reward(), expected_reward)

    def test_micro2(self):
        for _ in range(10):
            learner = TestMicro2Learner()
            messenger = task_messenger(micro.Micro2Task)
            self.basic_run(messenger, learner, 52)
            self.assertGreater(messenger.get_cumulative_reward(), 0)

    def test_micro3(self):
        for _ in range(10):
            learner = TestMicro3Learner()
            messenger = task_messenger(micro.Micro3Task)
            self.basic_run(messenger, learner, 1089)    # 33*33
            cum_reward = messenger.get_cumulative_reward()
            self.assertGreater(cum_reward, -1090)
            self.basic_run(messenger, learner, 1)
            self.assertEqual(cum_reward + 1, messenger.get_cumulative_reward())

    def test_micro4(self):
        for _ in range(10):
            learner = TestMicro1Learner()
            messenger = task_messenger(micro.Micro4Task)
            self.basic_run(messenger, learner, 10)
            self.assertEqual(messenger.get_cumulative_reward(), 10)
