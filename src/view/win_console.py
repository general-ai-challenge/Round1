from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import locale
from core.channels import InputChannel
import os

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()

# Uncle Google
def get_console_size():
    from ctypes import windll, create_string_buffer

    # stdin handle is -10
    # stdout handle is -11
    # stderr handle is -12

    h = windll.kernel32.GetStdHandle(-12)
    csbi = create_string_buffer(22)
    res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

    if res:
        import struct
        (bufx, bufy, curx, cury, wattr,
        left, top, right, bottom, maxx, maxy) = \
            struct.unpack("hhhhHhhhhhh", csbi.raw)
        sizex = right - left + 1
        sizey = bottom - top + 1
    else:
        # can't determine actual size
        # return default values
        sizex, sizey = 80, 25 
        
    return sizey, sizex

class StdOutView(object):

    def __init__(self, env, session):
        self._env = env
        self._session = session

        # observe basic high level information about the session and environment
        env.task_updated.register(
            self.on_task_updated)
        session.total_reward_updated.register(
            self.on_total_reward_updated)
        session.total_time_updated.register(
            self.on_total_time_updated)

        self.logger = logging.getLogger(__name__)
        # we save information for display later
        self.info = {'reward': 0, 'time': 0, 'current_task': 'None'}

    def on_total_reward_updated(self, reward):
        self.info['reward'] = reward

    def on_total_time_updated(self, time):
        self.info['time'] = time

    def on_task_updated(self, task):
        if 'current_task' in self.info:
            print('Current_task: {0}'.format(task.get_name()))

    def initialize(self):
        pass

    def finalize(self):
        pass


class StdInOutView(StdOutView):

    def __init__(self, env, session, serializer, show_world=False):
        super(StdInOutView, self).__init__(env, session)

        # for visualization purposes, we keep an internal buffer of the
        # input and output stream so when they are cleared from task to
        # task, we can keep the history intact.
        self.input_buffer = ''
        self.output_buffer = ''
        self.panic = 'SKIP'
        # record what the learner says
        self._learner_channel = InputChannel(serializer)
        # record what the environment says
        self._env_channel = InputChannel(serializer)
        # listen to the updates in these channels
        self._learner_channel.sequence_updated.register(
            self.on_learner_sequence_updated)
        self._learner_channel.message_updated.register(
            self.on_learner_message_updated)
        self._env_channel.sequence_updated.register(
            self.on_env_sequence_updated)
        self._env_channel.message_updated.register(
            self.on_env_message_updated)
        if show_world:
            # register a handler to plot the world if show_world is active
            env.world_updated.register(
                self.on_world_updated)
        # connect the channels with the observed input bits
        session.env_token_updated.register(self.on_env_token_updated)
        session.learner_token_updated.register(self.on_learner_token_updated)
        del self.info['current_task']

    def on_env_token_updated(self, token):
        self._env_channel.consume_bit(token)

    def on_learner_token_updated(self, token):
        self._learner_channel.consume_bit(token)

    def on_learner_message_updated(self, message):
        # we use the fact that messages arrive character by character
        if self._learner_channel.get_text():
            self.input_buffer += self._learner_channel.get_text()[-1]
            self.input_buffer = self.input_buffer[-self._scroll_msg_length:]
            self._learner_input = self.channel_to_str(
                self.input_buffer,
                self._learner_channel.get_undeserialized())

    def on_learner_sequence_updated(self, sequence):
        self._learner_input = self.channel_to_str(
            self.input_buffer,
            self._learner_channel.get_undeserialized())

    def on_env_message_updated(self, message):
        if self._env_channel.get_text():
            self.output_buffer += \
                self._env_channel.get_text()[-1]
            self.output_buffer = self.output_buffer[-self._scroll_msg_length:]
            self.env_output = self.channel_to_str(
                self.output_buffer,
                self._env_channel.get_undeserialized())

    def on_env_sequence_updated(self, sequence):
        self._env_output = self.channel_to_str(
            self.output_buffer,
            self._env_channel.get_undeserialized())

    def on_world_updated(self, world):
        if world:
            world.state_updated.register(self.on_world_state_updated)

    def on_world_state_updated(self, world):
        pass
        print(str(world))

    def initialize(self):
        rows, columns = get_console_size()
        reward_len = 15
        self._total_msg_length = columns - 1
        self._scroll_msg_length = columns - 1 - reward_len


    def get_input(self):
        print("_"*self._total_msg_length)
        print(self._env_output + ' reward:{:7}'.format(self.info['reward']))
        print(self._learner_input + ' time:{:9}'.format(self.info['time']))
        # printed
        real_raw_input = vars(__builtins__).get('raw_input', input)
        inputstr = real_raw_input()
        if inputstr == self.panic:
            inputstr = ''
            self._env._task_time = float('inf')
        return inputstr

    def channel_to_str(self, text, bits):
        length = self._scroll_msg_length - 10
        if length <= 1:
            raise Exception('The command window is too small.')
        return "{0:_>{length}}[{1: <8}]".format(
            text[-length:], bits[-7:], length=length)
