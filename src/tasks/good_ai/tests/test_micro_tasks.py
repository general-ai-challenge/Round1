import contextlib
import unittest

from core.byte_channels import ByteInputChannel, ByteOutputChannel
import core.environment as environment
import core.serializer as serializer
from learners.base import BaseLearner
from tasks.competition.tests.helpers import SingleTaskScheduler
from tasks.good_ai.micro import Micro1Task


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
        return nbits

    def get_text(self):
        return self._input_channel.get_text()

    def get_cumulative_reward(self):
        return self.cum_reward


@contextlib.contextmanager
def task_messenger(task_funct):
    slzr = serializer.StandardSerializer()
    task = task_funct()
    scheduler = SingleTaskScheduler(task)
    env = environment.Environment(slzr, scheduler, byte_mode=True)
    m = EnvironmentByteMessenger(env, slzr)
    yield m


class TestMicro1Learner(BaseLearner):
    pass


class TestMicroTask(unittest.TestCase):

    def test_run(self):
        learner = TestMicro1Learner()
        with task_messenger(Micro1Task) as m:
            for _ in range(10):
                question = m.get_text()[-1]
                # print("question read {}".format(repr(question)))
                answer = learner.next(question)
                # print("answer read {}".format(repr(answer)))
                m.send(answer)
                reward = m.get_cumulative_reward()
                # print("reward read {}".format(reward))
                learner.reward(reward)
            self.assertEqual(m.get_cumulative_reward(), 10)
