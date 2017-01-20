from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from core.task import on_start, on_message, on_timeout
from tasks.competition.base import BaseTask
import tasks.competition.messages as msg
import random
import string


def random_string(length):
    return "".join(random.choice(string.ascii_uppercase) for _ in range(length))


def replace_char(c):
    candidates = list(string.ascii_uppercase)
    candidates.remove(c)
    return "".join(random.choice(candidates))


def change_string_randomly(astring):
    length = len(astring)

    nr_of_changes = random.randint(1, length)
    to_change = range(length)
    to_change = random.sample(to_change, nr_of_changes)

    new_string = list(astring)
    for i in to_change:
        new_string[i] = replace_char(new_string[i])

    return "".join(new_string)


class TaskSet1(BaseTask):
    def __init__(self, world=None):
        super(TaskSet1, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):

        length_of_description = random.randint(1, 3)
        description = random_string(length_of_description)

        is_correct = random.choice([True, False])

        verify_multiply = random.randint(1, 3)
        verify = "".join([description] * verify_multiply)
        if not (is_correct):
            verify = change_string_randomly(verify)

        self.answer = "true" if is_correct else "false"

        self.give_away_message = 'Wrong. The right answer is: {answer}.'.format(
            answer=self.answer
        )

        self.set_message("description: {description}; verify: {verify}." \
            .format(
            description=description,
            verify=verify
        ))

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
