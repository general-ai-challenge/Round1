# -*- coding: utf-8
# 'version': '0.3'
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.
# TODO task, competition.base unresolved ref
from core.task import on_start, on_message, on_timeout
from tasks.competition.base import BaseTask
import tasks.competition.messages as msg
import random

# global data structures to be called by multiple tasks

# a dictionary with all possible objects in the vocabulary
vocabulary = {0: "apple", 1: "banana", 2: "beet", 3: "carrot", 4: "cucumber", 5: "mango", 6: "onion", 7: "pear",
              8: "pineapple", 9: "potato", 10: "tomato"}

# maximum number of objects to list
max_total = 10

vocab_size = len(vocabulary)


class SimpleCountingTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(SimpleCountingTask, self).__init__(world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        # TODO event not used
        """ # pick how many objects in total will be described # for last object change separator from "," to "and"
         # pick object # build up message # update counter # pick object to ask the question
        :param event:
        :return:
        """
        separator = ""
        counter = {}
        partial_message = ""
        total = random.randint(1, max_total)
        for i in range(0, total):
            if i == total - 2:
                separator = " and "
            elif i == total - 1:
                separator = ""
            else:
                separator = ", "
            obj = vocabulary[random.randint(1, vocab_size - 1)]
            partial_message += msg.indef_article(obj)
            partial_message += separator
            if obj not in counter:
                counter[obj] = 0
            counter[obj] += 1
        object_in_question = vocabulary[random.randint(1, vocab_size - 1)]
        self.answer = msg.numbers_in_words[counter.get(object_in_question, 0)]
        self.give_away_message = 'Wrong. The right answer is: {answer}.'.format(answer=self.answer)
        self.set_message("I have {listing_objects}. How many {object} do I have? ".format(
                listing_objects=partial_message, object=msg.pluralize(object_in_question, 2)))

    @on_message(r'\.')
    def check_response(self, event):
        """ # check if given answer matches  # if the message sent by the learner equals the teacher's # expected
        answer followed by a period, reward the learner. # If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.answer, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """ # if the learner has not produced any plausible answer by the max_time allowed, fail the learner sending
        appropriate feedback.

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """fail the learner sending a random fail feedback message

        :return:
        """
        self.set_result(0, self.give_away_message)
