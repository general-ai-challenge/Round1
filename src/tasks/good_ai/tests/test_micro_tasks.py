import string
import unittest

from core.byte_channels import ByteInputChannel, ByteOutputChannel
from core.scheduler import ConsecutiveTaskScheduler
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


def basic_task_run(messenger, learner, task):
    while True:
        question = messenger.get_text()[-1]
        answer = learner.next(question)
        reward = messenger.send(answer)
        learner.reward(reward)
        if task.agent_solved_instance() is not None:
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
        basic_task_run(self.messenger, learner, first_task)
        # I should have two rewards now
        self.assertEqual(self.scheduler.reward_count, 2)
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
        self.assertIsNotNone(first_task)
        learner = BaseLearner()
        self.env.task_updated.register(on_task_change)
        basic_task_run(self.messenger, learner, first_task)     # failure should be issued now
        self.messenger.send()   # now the task is overdue
        self.messenger.send()   # force the control loop to enter next task
        self.assertTrue(task_changed[0])
        self.assertEqual(self.env._current_task, first_task)
        self.assertEqual(self.scheduler.reward_count, 0)


class TestMicroTask(unittest.TestCase):

    def test_stupid_agent(self):
        task = micro.Micro1Task()
        learner = BaseLearner()
        messenger = task_messenger(task)
        basic_task_run(messenger, learner, task)
        self.assertFalse(task.agent_solved_instance())

    def test_micro2(self):
        for _ in range(10):
            learner = TestMicro1Learner(string.ascii_lowercase, True)
            task = micro.Micro2Task()
            messenger = task_messenger(task)
            basic_task_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance())

    def test_micro3(self):
        for _ in range(10):
            learner = TestMicro3Learner()
            task = micro.Micro3Task()
            messenger = task_messenger(task)
            basic_task_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance())

    def test_micro4(self):
        for _ in range(10):
            task = micro.Micro4Task()
            learner = BaseLearner()
            messenger = task_messenger(task)
            basic_task_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance())

    def test_micro5sub1(self):
        for _ in range(10):
            task = micro.Micro5Sub1Task()
            learner = TestMicro5Sub1Learner()
            messenger = task_messenger(task)
            basic_task_run(messenger, learner, task)
            self.assertTrue(task.agent_solved_instance())


class TestMicroTaskBase(unittest.TestCase):

    task = None

    @classmethod
    def setUpClass(cls):
        if cls is TestMicroTaskBase:
            raise unittest.SkipTest("Skip MicroTaskBase tests, it's a base class")
        super(TestMicroTaskBase, cls).setUpClass()

    def _get_learner(self):
        pass

    def init_env(self, success_threshold=2):
        slzr = serializer.StandardSerializer()
        scheduler = ConsecutiveTaskScheduler([self.task], success_threshold)
        env = environment.Environment(slzr, scheduler, max_reward_per_task=float("inf"), byte_mode=True)
        messenger = EnvironmentByteMessenger(env, slzr)
        return (scheduler, messenger)

    def test_task(self):
        for _ in range(10):
            learner = self._get_learner()
            messenger = task_messenger(self.task)
            basic_task_run(messenger, learner, self.task)
            self.assertTrue(self.task.agent_solved_instance())

    def test_successful_evaluation(self):
        '''
        Tests that task instance can be solved and that there are no residuals from 1st instance, which would prevent agent from solving 2nd instance
        '''
        scheduler, messenger = self.init_env()
        # first run
        learner = TestMicro1Learner(self.task.alphabet)
        basic_task_run(messenger, learner, self.task)
        self.assertTrue(self.task.agent_solved_instance())
        self.assertEqual(scheduler.reward_count, 1)

        messenger.send()
        # second run
        learner = TestMicro1Learner(self.task.alphabet)
        basic_task_run(messenger, learner, self.task)
        self.assertTrue(self.task.agent_solved_instance())
        self.assertEqual(scheduler.reward_count, 2)

    def test_failed_evaluation(self):
        '''
        Tests that instance can be failed and that there are no residuals from 1st instance, which would solve the 2nd instance instead of agent
        '''
        scheduler, messenger = self.init_env()
        # first run
        learner = BaseLearner()
        basic_task_run(messenger, learner, self.task)
        self.assertFalse(self.task.agent_solved_instance())
        self.assertEqual(scheduler.reward_count, 0)

        messenger.send()
        # second run
        basic_task_run(messenger, learner, self.task)
        self.assertFalse(self.task.agent_solved_instance())
        self.assertEqual(scheduler.reward_count, 0)

    def test_failed_then_successful_evaluation(self):
        '''
        Tests that instance can be failed and that there are no residuals from 1st instance, which would prevent agent from solving 2nd instance
        '''
        scheduler, messenger = self.init_env()
        # first run
        learner = BaseLearner()
        basic_task_run(messenger, learner, self.task)
        self.assertFalse(self.task.agent_solved_instance())
        self.assertEqual(scheduler.reward_count, 0)

        messenger.send()
        # second run
        learner = TestMicro1Learner(self.task.alphabet)
        basic_task_run(messenger, learner, self.task)
        self.assertTrue(self.task.agent_solved_instance())
        self.assertEqual(scheduler.reward_count, 1)


class TestMicro1(TestMicroTaskBase):
    task = micro.Micro1Task()

    def _get_learner(self):
        return TestMicro1Learner(self.task.alphabet)
