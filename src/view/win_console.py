from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import logging
import locale

from core.byte_channels import ByteInputChannel, ByteOutputChannel
from core.channels import InputChannel
import sys
import os
import platform

import platform
if platform.python_version_tuple()[0] == '2':
    from kitchen.text.converters import to_unicode

locale.setlocale(locale.LC_ALL, '')
code = locale.getpreferredencoding()


def get_console_size():
    try:
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
            return sizey, sizex
    except ImportError:
        pass
    if platform.system() == 'Linux':
        sizex, sizey = os.popen('stty size', 'r').read().split()
        return int(sizex), int(sizey)

    # default values
    return 25, 140


class WinBaseView(object):

    NEXT_UPDATE = 1000

    def __init__(self, env, session):
        self._env = env
        self._session = session
        self._last_update = 0

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
            if self.info['current_task'] != task.get_name():
                self.info['current_task'] = task.get_name()

    def print_info(self):
        print('Time {}; Current task: {}; Reward {}.'.format(self.info['time'], self.info['current_task'],
                                                             self.info['reward']))

    def initialize(self):
        pass

    def finalize(self):
        pass


class StdOutView(WinBaseView):
    def __init__(self, env, session):
        super(StdOutView, self).__init__(env, session)

    def on_total_reward_updated(self, reward):
        super(StdOutView, self).on_total_reward_updated(reward)
        self.print_info()

    def on_total_time_updated(self, time):
        super(StdOutView, self).on_total_time_updated(time)
        if self._last_update + self.NEXT_UPDATE <= time:
            self._last_update = time
            self.print_info()

    def on_task_updated(self, task):
        if self.info['current_task'] != task.get_name():
            self.info['current_task'] = task.get_name()
            print('Change of a current task to: {} in time {}'.format(task.get_name(), self.info['time']))


class StdInOutView(WinBaseView):

    def __init__(self, env, session, serializer, show_world=False, byte_channels=False):
        super(StdInOutView, self).__init__(env, session)

        # for visualization purposes, we keep an internal buffer of the
        # input and output stream so when they are cleared from task to
        # task, we can keep the history intact.
        self.input_buffer = ''
        self.output_buffer = ''
        self.panic = u'SKIP'
        self.quit = 'QUIT'
        self._byte_channels = byte_channels

        if byte_channels:
            # record what the learner says
            self._learner_channel = ByteInputChannel(serializer)
            # record what the environment says
            self._env_channel = ByteInputChannel(serializer)
            # reward buffer
            self._reward_buffer = ''
        else:
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

    def on_total_reward_updated(self, reward):
        change = reward - self.info['reward']
        self.info['reward'] = reward
        if self._byte_channels:
            self._reward_buffer = self._reward_buffer[0:-1]
            self._reward_buffer += self._encode_reward(change)
            self._reward = self.channel_to_str(
                self._reward_buffer + ' ',
                self._env_channel.get_undeserialized())

    @staticmethod
    def _encode_reward(reward):
        d = {0: " ", 1: "+", -1: "-", 2: "2", -2: "\u01BB"}
        return d[reward]

    def on_env_token_updated(self, token):
        self._env_channel.consume(token)

    def on_learner_token_updated(self, token):
        self._learner_channel.consume(token)

    def on_learner_message_updated(self, message):
        # we use the fact that messages arrive character by character
        if self._learner_channel.get_text():
            self.input_buffer += self._learner_channel.get_text()[-1]
            self.input_buffer = self.input_buffer[-self._scroll_msg_length:]
            self._learner_input = self.channel_to_str(
                self.input_buffer + ' ',
                self._learner_channel.get_undeserialized())
            if self._byte_channels:
                self._reward_buffer += ' '
                self._reward = self.channel_to_str(
                    self._reward_buffer + ' ',
                    self._env_channel.get_undeserialized())

    def on_learner_sequence_updated(self, sequence):
        self._learner_input = self.channel_to_str(
            self.input_buffer + ' ',
            self._learner_channel.get_undeserialized())

    def on_env_message_updated(self, message):
        if self._env_channel.get_text():
            self.output_buffer += \
                self._env_channel.get_text()[-1]
            self.output_buffer = self.output_buffer[-self._scroll_msg_length:]
            self._env_output = self.channel_to_str(
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
        # properties init
        self._learner_input = self.channel_to_str(
            ' ',
            self._learner_channel.get_undeserialized())

    def get_input(self):
        print("_"*self._total_msg_length)
        print(self._env_output + ' reward:{:7}'.format(self.info['reward']))
        print(self._learner_input + ' time:{:9}'.format(self.info['time']))
        if self._byte_channels:
            print(self._reward)
        _ver = sys.version_info
        if _ver[0] == 2:
            input_str = raw_input()
        else:
            input_str = input()
        if platform.python_version_tuple()[0] == '2':
            input_str = to_unicode(input_str)
        if input_str == self.panic:
            input_str = ''
            self._env._task_time = float('inf')
        elif input_str == self.quit:
            sys.exit()
        return input_str

    def channel_to_str(self, text, bits):
        length = self._scroll_msg_length - 10
        if length <= 1:
            raise Exception('The command window is too small.')
        return "{0:_>{length}}[{1: <8}]".format(
            text[-length:], bits[-7:], length=length)
