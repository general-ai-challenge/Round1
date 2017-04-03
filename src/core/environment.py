# Copyright (c) 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.events import EventManager
from core.task import StateChanged, MessageReceived, \
    SequenceReceived, OutputSequenceUpdated, OutputMessageUpdated
from core.obs.observer import Observable
from core.serializer import ScramblingSerializerWrapper
from core.channels import InputChannel, OutputChannel
from core.byte_channels import ByteInputChannel, ByteOutputChannel
from collections import defaultdict
import logging


class Environment:
    '''
    The Environment is the one that communicates with the Learner,
    interpreting its output and reacting to it. The interaction is governed
    by an ongoing task which is picked by a TaskScheduler object.

    :param serializer: a Serializer object that translates text into binary and
        back.
    :param task_scheduler: a TaskScheduler object that determines which task
        is going to be run next.
    :param scramble: if True, the words outputted by the tasks are randomly
        scrambled.
    :param max_reward_per_task: maximum amount of reward that a learner can
        receive for a given task.
    '''

    def __init__(self, serializer, task_scheduler, scramble=False,
                 max_reward_per_task=10000, byte_mode=False):
        # save parameters into member variables
        self._task_scheduler = task_scheduler
        self._serializer = serializer
        self._max_reward_per_task = max_reward_per_task
        # cumulative reward per task
        self._reward_per_task = defaultdict(int)
        # the event manager is the controller that dispatches
        # changes in the environment (like new inputs or state changes)
        # to handler functions in the tasks that tell the environment
        # how to react
        self.event_manager = EventManager()
        # intialize member variables
        self._current_task = None
        self._current_world = None

        if scramble:
            serializer = ScramblingSerializerWrapper(serializer)
        if byte_mode:
            # we hear to our own output
            self._output_channel_listener = ByteInputChannel(serializer)
            # output channel
            self._output_channel = ByteOutputChannel(serializer)
            # input channel
            self._input_channel = ByteInputChannel(serializer)
        else:
            # we hear to our own output
            self._output_channel_listener = InputChannel(serializer)
            # output channel
            self._output_channel = OutputChannel(serializer)
            # input channel
            self._input_channel = InputChannel(serializer)
        # priority of ongoing message
        self._output_priority = 0
        # reward that is to be given at the learner at the end of the task
        self._reward = None
        self._result = None
        self._last_result = None
        # reward that is to be given immediately
        self._immediate_reward = None
        # Current task time
        self._task_time = None
        # Task separator issued
        self._task_separator_issued = False
        # Internal logger
        self.logger = logging.getLogger(__name__)

        # signals
        self.world_updated = Observable()
        self.task_updated = Observable()

        # Register channel observers
        self._input_channel.sequence_updated.register(
            self._on_input_sequence_updated)
        self._input_channel.message_updated.register(
            self._on_input_message_updated)
        self._output_channel_listener.sequence_updated.register(
            self._on_output_sequence_updated)
        self._output_channel_listener.message_updated.register(
            self._on_output_message_updated)

    def next(self, learner_input):
        '''Main loop of the Environment. Receives one bit from the learner and
        produces a response (also one bit)'''

        self._last_result = None  # will be set while execution is inside this function or its child tree

        # Make sure we have a task
        if not self._current_task:
            self._switch_new_task()

        # If the task has not reached the end by either Timeout or
        # achieving the goal
        if not self._current_task.has_ended():
            reward = None
            # Check if a Timeout occurred
            self._current_task.check_timeout(self._task_time)
            # Process the input from the learner and raise events
            if learner_input is not None:
                # record the input from the learner and deserialize it
                # TODO this bit is dropped otherwise on a timeout...
                self._input_channel.consume(learner_input)
                # switch to next task immediately if this input caused the task to end
                # and there is no feedback to output (output_channel is empty)
                if self._current_task.has_ended() and self._output_channel.is_empty():
                    self._switch_new_task()
            # We are in the middle of the task, so no rewards are given
        else:
            # If the task is ended and there is nothing else to say,
            # issue a silence and then return reward and move to next task
            if self._output_channel.is_empty():
                if self._task_separator_issued or self._should_skip_separator():
                    # Have nothing more to say
                    # reward the learner if necessary and switch to new task
                    reward = self._reward if self._reward is not None else 0
                    self._switch_new_task()
                    self._task_separator_issued = False
                else:
                    self._output_channel.set_message(
                        self._serializer.SILENCE_TOKEN)
                    self._task_separator_issued = True
                    reward = None
            else:
                # TODO: decide what to do here.
                # Should we consume the bit or not?
                self._input_channel.consume(learner_input)
                # If there is still something to say, continue saying it
                reward = None
        # Get one bit from the output buffer and ship it
        if self._output_channel.is_empty():
            self._output_channel.set_message(self._serializer.SILENCE_TOKEN)
        output = self._output_channel.consume()

        # we hear to ourselves
        self._output_channel_listener.consume(output)
        # advance time
        self._task_time += 1

        if self._immediate_reward is not None and reward is None:
            reward = self._immediate_reward
            self._immediate_reward = None
        if reward is not None:
            # process the reward (clearing it if it's not allowed)
            reward = self._allowable_reward(reward)
        else:
            reward = 0

        return output, reward

    def get_reward_per_task(self):
        '''
        Returns a dictonary that contains the cumulative reward for each
        task.
        '''
        return self._reward_per_task

    def _allowable_reward(self, reward):
        '''Checks if the reward is allowed within the limits of the
        `max_reward_per_task` parameter, and resets it to 0 if not.'''
        task_name = self._current_task.get_name()
        if self._reward_per_task[task_name] < self._max_reward_per_task:
            self._reward_per_task[task_name] += reward
            return reward
        else:
            return 0

    def is_silent(self):
        '''
        Tells if the environment is sending any information through the output
        channel.
        '''
        return self._output_channel.is_silent()

    def _on_input_sequence_updated(self, sequence):
        if self.event_manager.raise_event(SequenceReceived(sequence)):
            self.logger.debug("Sequence received by running task: '{0}'".format(
                sequence))

    def _on_input_message_updated(self, message):
        # send the current received message to the task
        if self.event_manager.raise_event(MessageReceived(
                message)):
            self.logger.debug("Message received by running task: '{0}'".format(
                message))

    def _on_output_sequence_updated(self, sequence):
        self.event_manager.raise_event(OutputSequenceUpdated(sequence))

    def _on_output_message_updated(self, message):
        self.event_manager.raise_event(OutputMessageUpdated(message))

    def _should_skip_separator(self):
        return hasattr(self._current_task, 'skip_task_separator') and self._current_task.skip_task_separator

    def set_result(self, result, message='', priority=0, provide_result_as_reward=True):
        # the following two ifs prevent repeating the same feedback ad infinitum, which otherwise happens in mini-tasks
        # in case of a repeated invalid input. self._result is set back to None every time a new task is switched.
        if self._result is True and result is True:
            return
        if self._result is False and result is False:
            return

        if provide_result_as_reward:
            self._reward = result
        self._result = result
        self._current_task.end()
        self.logger.debug('Terminating instance with result {0} with message "{1}"'
                          ' and priority {2}'
                          .format(result, message, priority))
        # adds a final space to the final message of the task
        # to separate the next task instructions
        self.set_message(message, priority)

    def set_immediate_reward(self, reward):
        '''Sets the reward immediately'''
        self._immediate_reward = reward
        self.logger.debug('Setting immediate reward {}'.format(reward))

    def set_message(self, message, priority=0):
        ''' Saves the message in the output buffer so it can be delivered
        bit by bit. It overwrites any previous content.
        '''
        if self._output_channel.is_empty() or priority >= self._output_priority:
            self.logger.debug('Setting message "{0}" with priority {1}'
                              .format(message, priority))
            self._output_channel.set_message(message)
            self._output_priority = priority
        else:
            self.logger.info(
                'Message "{0}" blocked because of '
                'low priority ({1}<{2}) '.format(
                    message, priority, self._output_priority)
            )

    def raise_event(self, event):
        return self.event_manager.raise_event(event)

    def raise_state_changed(self):
        '''
            This rases a StateChanged Event, meaning that something
            in the state of the world or the tasks changed (but we
            don't keep track what)
        '''
        # state changed events can only be raised if the current task is
        # started
        if self._current_task and self._current_task.has_started():
            # tasks that have a world should also take the world state as
            # an argument
            if self._current_world:
                self.raise_event(StateChanged(
                    self._current_world.state, self._current_task.state))
            else:
                self.raise_event(StateChanged(self._current_task.state))
            return True
        return False

    def _switch_new_task(self):
        '''
        Asks the task scheduler for a new task,
        reset buffers and time, and registers the event handlers
        '''
        # deregister previous event managers
        if self._current_task:
            self._current_task.deinit()
            self._deregister_task_triggers(self._current_task)

        # pick a new task
        if self._result != None:
            self._last_result = self._result
            self._task_scheduler.reward(self._result)
            self._result = None

        self._current_task = self._task_scheduler.get_next_task()
        try:
            # This is to check whether the user didn't mess up in instantiating
            # the class
            self._current_task.get_world()
        except TypeError:
            raise RuntimeError("The task {0} is not correctly instantiated. "
                               "Are you sure you are not forgetting to "
                               "instantiate the class?".format(
                                   self._current_task))
        self.logger.debug("Starting new task: {0}".format(self._current_task))

        # check if it has a world:
        if self._current_task.get_world() != self._current_world:
            # if we had an ongoing world, end it.
            if self._current_world:
                self._current_world.end()
                self._deregister_task_triggers(self._current_world)
            self._current_world = self._current_task.get_world()
            if self._current_world:
                # register new event handlers for the world
                self._register_task_triggers(self._current_world)
                # initialize the new world
                self._current_world.start(self)
            self.world_updated(self._current_world)
        # reset state
        self._task_time = 0
        self._reward = None
        self._input_channel.clear()
        self._output_channel.clear()
        self._output_channel_listener.clear()
        # register new event handlers
        self._register_task_triggers(self._current_task)
        # start the task, sending the current environment
        # so it can interact by sending back rewards and messages
        self._current_task.start(self)
        self.task_updated(self._current_task)

    def _deregister_task_triggers(self, task):
        for trigger in task.get_triggers():
            try:
                self.event_manager.deregister(task, trigger)
            except ValueError:
                # if the trigger was not registered, we don't worry about it
                pass
            except KeyError:
                # if the trigger was not registered, we don't worry about it
                pass
        task.clean_dynamic_handlers()

    def _register_task_triggers(self, task):
        for trigger in task.get_triggers():
            self._register_task_trigger(task, trigger)

    def _register_task_trigger(self, task, trigger):
        self.event_manager.register(task, trigger)
