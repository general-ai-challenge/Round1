from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import string

from core.task import on_message, on_start, on_timeout

from fsa import build_automaton

from tasks.competition.base import BaseTask
import tasks.competition.messages as msg


def random_string(length):
    return "".join(random.choice(string.ascii_uppercase) for _ in range(length))


class TaskSet1(BaseTask):

    def __init__(self, world=None):
        super(TaskSet1, self).__init__(world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        length_of_description = random.randint(1, 3)
        description = random_string(length_of_description)
        is_correct = random.choice([True, False])
        automaton = build_automaton(description, "and")

        if is_correct:
            verify = automaton.get_correct_string()
        else:
            verify = automaton.get_wrong_string()

        self.answer = "true" if is_correct else "false"
        self.give_away_message = 'Wrong. The right answer is: {}.'.format(self.answer)
        self.set_message("description: {}; verify: {}.".format(description, verify))

    @on_message(r'\.')
    def check_response(self, event):
        # check if given answer matches
        if event.is_message(self.answer, '.'):
            # if the message sent by the learner equals the teacher's
            # expected answer followed by a period, reward the learner.
            self.set_reward(1, random.choice(msg.congratulations))
        else:
            # If the learner said anything else, it fails the task.
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.
        self.fail_learner()

    def fail_learner(self):
        # fail the learner sending a random fail feedback message
        self.set_reward(0, self.give_away_message)
