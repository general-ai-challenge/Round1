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
    return random_string_from(length, string.ascii_uppercase)


def random_string_from(length, subset):
    return "".join(random.choice(subset) for _ in range(length))


# generovat incorrect z distribuce correct
# pridat minimalni delku
def get_task(max_length_of_description, max_nr_of_groups, max_length_of_verify, description_type,
             not_portion=None, subset_size=None, without_anything=None):
    not_portion = not_portion or 0
    subset_size = subset_size or 13

    if not description_type == "and" and not description_type == "or":
        print("Unknown description_type: {}".format(description_type))
        return
    if subset_size > 13:
        print("Subset size cannot be higher than 13.")
        return

    nr_of_groups = random.randint(1, max_nr_of_groups)
    if not_portion > 0:
        alphabet = string.ascii_uppercase
        normal_subset = "".join(random.choice(alphabet) for _ in range(subset_size))
        reduced_alphabet = "".join([char for char in alphabet if char not in normal_subset])
        not_subset = "".join(random.choice(reduced_alphabet) for _ in range(subset_size))

    descriptions = []
    if without_anything:
        has_anything = False
    else:
        has_anything = random.choice([True, False])

    if description_type == "or" and not without_anything:
        if random.random() < 0.05:
            has_anything = True
            nr_of_groups = 0
        else:
            has_anything = False

    for _ in range(nr_of_groups):
        length_of_description = random.randint(1, max_length_of_description)
        if not_portion > 0:
            if random.random() < not_portion:
                description = "not " + random_string_from(length_of_description, not_subset)
                has_anything = True
            else:
                description = random_string_from(length_of_description, normal_subset)
        else:
            description = random_string(length_of_description)
        descriptions.append(description)

    if has_anything:
        descriptions.append("anything")

    descriptions = list(set(descriptions))
    automaton = build_automaton(" ".join(descriptions), description_type)
    type_connection = " {} ".format(description_type)
    complete_description = type_connection.join(descriptions)
    is_correct = random.choice([True, False])

    verify_length = random.randint(1, max_length_of_verify)
    if is_correct:
        verify = automaton.get_correct_string(verify_length)
    else:
        verify = automaton.get_wrong_string(verify_length, 0)
    return (is_correct, "description: {}; verify {}".format(complete_description, verify))


class TaskSetBase(BaseTask):

    def __init__(self, world=None):
        super(TaskSetBase, self).__init__(world=world, max_time=3000)
        self.max_length_of_description = None
        self.max_nr_of_groups = None
        self.max_length_of_verify = None
        self.description_type = None
        self.not_portion = None
        self.subset_size = None
        self.without_anything = None

    @on_start()
    def give_instructions(self, event):
        if not self.max_length_of_description or not self.max_nr_of_groups or not self.max_length_of_verify or not self.description_type:
            raise AttributeError("Some of the TaskSet attributes are not set!")

        is_correct, task = get_task(self.max_length_of_description, self.max_nr_of_groups, self.max_length_of_verify,
                                    self.description_type, self.not_portion, self.subset_size, self.without_anything)

        self.answer = "true" if is_correct else "false"
        self.give_away_message = 'Wrong. The right answer is: {}.'.format(self.answer)
        self.set_message(task)

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


class TaskSet1(TaskSetBase):

    def __init__(self, world=None):
        super(TaskSet1, self).__init__(world=world)
        self.max_length_of_description = 3
        self.max_nr_of_groups = 1
        self.max_length_of_verify = 10
        self.description_type = "and"
        self.without_anything = True


class TaskSet2(TaskSetBase):

    def __init__(self, world=None):
        super(TaskSet2, self).__init__(world=world)
        self.max_length_of_description = 3
        self.max_nr_of_groups = 3
        self.max_length_of_verify = 10
        self.description_type = "or"


class TaskSet3(TaskSetBase):

    def __init__(self, world=None):
        super(TaskSet3, self).__init__(world=world)
        self.max_length_of_description = 3
        self.max_nr_of_groups = 3
        self.max_length_of_verify = 30
        self.description_type = "and"


class TaskSet4(TaskSetBase):

    def __init__(self, world=None):
        super(TaskSet4, self).__init__(world=world)
        self.max_length_of_description = 3
        self.max_nr_of_groups = 3
        self.max_length_of_verify = 30
        self.description_type = "and"
        self.not_portion = 0.5
