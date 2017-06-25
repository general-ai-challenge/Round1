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
from core.task import Task, on_start, on_message, on_sequence,\
    on_state_changed, on_timeout, on_output_message
from tasks.competition.base import BaseTask
import tasks.competition.messages as msg
import random
import string
import itertools
import copy

# task-specific messages
verbs = ["say", "repeat"]
negation = ["do not", "don\'t"]

# FIXME: replace with association's objects and properties?
phrases = ["apple", "banana", "cat", "hello world"]
context = ["and you will get a reward", "and a reward is yours", "and you will pass this task",
           "and you will solve this problem"]
# repetition tasks configuration
repeat_min = 2
repeat_max = 3


class BeSilentTask(Task):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(BeSilentTask, self).__init__(world=world, max_time=random.randint(100, 1000))


    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# give instructions at the beginning of the task# initialize a variable to keep track if the learner has
         been failed

        :param event:
        :return:
        """
        self.flag_failed = False
        self.set_message(random.choice(["be silent now.",
                                        "do not say anything."]))


    @on_message("[^ ]")
    def on_message(self, event):
        # TODO event not used
        """# silence is represented by the space character catch any non-space character# if the learner produces
        anything but a space, it receives reward 0 and the task is over. We need to make sure to do this only once
        so for every incoming 1 bit we don't start again sending the feedback message.# set the flag, so we don't

        :param event:
        :return:
        """
        if not self.flag_failed:
            self.set_result(0, random.choice(msg.failed))
            self.flag_failed = True


    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """# when the maximum amount of time set for the task has elapsed# if the learner has been silent, it
        receives reward +1 and the task is over.

        :param event:
        :return:
        """
        self.set_result(1, random.choice(msg.congratulations))


class RepeatCharacterTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatCharacterTask, self).__init__(world=world, max_time=1000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# randomly sample a character to be repeated# ask the learner to repeat the phrase sampling one of the
        possible ways of asking that.

        :param event:
        :return:
        """
        self.cur_char = random.choice(string.ascii_letters)
        self.set_message("{query_verb} {phrase}."
                         .format(query_verb=random.choice(verbs), phrase=self.cur_char))


    @on_message(r'\.$')
    def on_message(self, event):
        """# we wait for the learner to send a message finalized by a full stop.# if the message sent by the learner
        equals the teacher's selected phrase followed by a period, reward the learner.# If the learner said anything
        else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.cur_char, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """# if the learner has not produced any plausible answer by the max_time allowed, fail the learner sending
        appropriate feedback.

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learner sending a random fail feedback message

        :return:
        """
        self.set_result(0, random.choice(msg.failed))


class RepeatWhatISayTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayTask, self).__init__(world=world, max_time=1000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# randomly sample a phrase# ask the learner to repeat the phrase sampling one of the possible
        # ways of asking that.

        :param event:
        :return:
        """
        self.cur_phrase = random.choice(phrases)
        self.set_message("{query_verb} {phrase}.".format(query_verb=random.choice(verbs), phrase=self.cur_phrase))

    # we wait for the learner to send a message finalized by a full stop.
    @on_message(r'\.$')
    def on_message(self, event):
        """# if the message sent by the learner equals the teacher's selected phrase followed by a period, reward
        the learner. # If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.cur_phrase, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """# if the learner has not produced any plausible answer by the max_time allowed, fail the learner
        sending appropriate feedback.

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learner sending a random fail feedback message

        :return:
        """
        self.set_result(0, random.choice(msg.failed))


class RepeatWhatISay2Task(BaseTask):
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISay2Task, self).__init__(world=world, max_time=1000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# sample a random phrase# ask the learner to repeat the phrase sampling one of the possible ways of
        asking that, and putting some context after the target.

        :param event:
        :return:
        """
        self.cur_phrase = random.choice(phrases)
        self.set_message("{query_verb} {phrase} {context}."
                         .format(query_verb=random.choice(verbs), phrase=self.cur_phrase, context=random.choice(context)))

    @on_message(r'\.$')
    def on_message(self, event):
        """# if the message sent by the learner equals the teacher's selected phrase followed by a period, reward
        the learner.# If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.cur_phrase, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """# if the learner has not produced any plausible answer by the max_time allowed, fail the learner
        sending appropriate feedback.

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learner sending a random fail feedback message

        :return:
        """
        self.set_result(0, random.choice(msg.failed))


class RepeatWhatISayMultipleTimesTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayMultipleTimesTask, self).__init__(world=world, max_time=10000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# sample a random phrase# sample the number of times it has to repeat the phrase (can be expressed in
        letters or numbers) # ask the learner to repeat the target phrase n times.# save the correct answer

        :param event:
        :return:
        """
        self.cur_phrase = random.choice(phrases)
        self.n = random.randint(repeat_min, repeat_max)
        self.set_message("{query_verb} {phrase} {times} times."
                         .format(query_verb=random.choice(verbs), phrase=self.cur_phrase,
                                 times=msg.number_to_string(self.n)))
        self.target = ' '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        """# if the message sent by the learner equals the teacher's selected phrase repeated n times followed by
        a period, reward the learner.# If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.target, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """# if the learner has not produced any plausible answer by the max_time allowed, fail the learner sending
        appropriate feedback.

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learner teaching it the correct answer

        :return:
        """
        self.set_result(0, "{negative_feedback} correct answer is: {answer}."
                        .format(negative_feedback=random.choice(msg.failed), answer=self.target))


class RepeatWhatISayMultipleTimes2Task(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayMultipleTimes2Task, self).__init__(world=world, max_time=10000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# sample a random phrase# sample the number of times it has to repeat the phrase
        # (can be expressed in letters or numbers)# save the correct answer

        :param event:
        :return:
        """
        self.cur_phrase = random.choice(phrases)
        self.n = random.randint(repeat_min, repeat_max)
        self.set_message("{query_verb} {phrase} {times} times {context}."
                         .format(query_verb=random.choice(verbs), phrase=self.cur_phrase,
                                 times=msg.number_to_string(self.n), context=random.choice(context)))
        self.target = ' '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        """# if the message sent by the learner equals the teacher's selected phrase repeated n times followed by
        a period, reward the learner.# If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.target, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learner if it hasn't repeated the message by the timeout

        :return:
        """
        self.set_result(0, "{negative_feedback} correct answer is: {answer}."
                        .format(negative_feedback=random.choice(msg.failed), answer=self.target))


class RepeatWhatISayMultipleTimesSeparatedByCommaTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayMultipleTimesSeparatedByCommaTask, self).__init__(world=world, max_time=10000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# sample a random phrase# sample the number of times it has to repeat the phrase (can be expressed in l
        etters or numbers)# save the correct answer

        :param event:
        :return:
        """
        self.cur_phrase = random.choice(phrases)
        self.n = random.randint(repeat_min, repeat_max)
        self.set_message("{query_verb} {phrase} {times} times separated "
                         "by comma (,)."
                         .format(query_verb=random.choice(verbs), phrase=self.cur_phrase,
                                 times=msg.number_to_string(self.n), context=random.choice(context)))
        self.target = ', '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        """# if the message sent by the learner equals the teacher's selected phrase repeated n times followed by
        a period, reward the learner.# If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.target, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learner if it hasn't repeated the message by the timeout

        :return:
        """
        self.set_result(0, "{negative_feedback} correct answer is: {answer}."
                        .format(negative_feedback=random.choice(msg.failed), answer=self.target))


class RepeatWhatISayMultipleTimesSeparatedByAndTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayMultipleTimesSeparatedByAndTask, self).__init__(world=world, max_time=10000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# sample a random phrase# sample the number of times it has to repeat the phrase (can be expressed in
        letters or numbers)# save the correct answer

        :param event:
        :return:
        """
        self.cur_phrase = random.choice(phrases)
        self.n = random.randint(repeat_min, repeat_max)
        self.set_message("{query_verb} {phrase} {times} times separated "
                         "by and."
                         .format(query_verb=random.choice(verbs), phrase=self.cur_phrase,
                                 times=msg.number_to_string(self.n), context=random.choice(context)))
        self.target = ' and '.join([self.cur_phrase] * self.n)

    @on_message(r'\.$')
    def on_message(self, event):
        """ # if the message sent by the learner equals the teacher's selected phrase repeated n times followed by
        a period, reward the learner.# If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.target, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learner if it hasn't repeated the message by the timeout

        :return:
        """
        self.set_result(0, "{negative_feedback} correct answer is: {answer}."
                        .format(negative_feedback=random.choice(msg.failed), answer=self.target))


class RepeatWhatISayMultipleTimesSeparatedByCATask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayMultipleTimesSeparatedByCATask, self).__init__(world=world, max_time=10000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# sample a random phrase# sample the number of times it has to repeat the phrase (can be expressed in
        letters or numbers)# save the correct answer

        :param event:
        :return:
        """
        self.cur_phrase = random.choice(phrases)
        self.n = random.randint(repeat_min, repeat_max)
        self.set_message("{query_verb} {phrase} {times} times separated "
                         "by comma and and."
                         .format(query_verb=random.choice(verbs), phrase=self.cur_phrase,
                                 times=msg.number_to_string(self.n), context=random.choice(context)))
        self.target = ' and '.join([", ".join([self.cur_phrase] * (self.n - 1)), self.cur_phrase])

    @on_message(r'\.$')
    def on_message(self, event):
        """# if the message sent by the learner equals the teacher's selected phrase repeated n times followed by
        a period, reward the learner.# If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.target, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """ # fail the learner if it hasn't repeated the message by the timeout

        :return:
        """
        self.set_result(0, "{negative_feedback} correct answer is: {answer}."
                        .format(negative_feedback=random.choice(msg.failed), answer=self.target))


class RepeatWhatISayDisjunction(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayDisjunction, self).__init__(world=world, max_time=3000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# randomly sample two objects# ask the learner to repeat the phrase sampling one of the possible
        # ways of asking that.# compute the answer

        :param event:
        :return:
        """
        self.cur_phrases = [random.choice(phrases), random.choice(phrases)]
        self.set_message("{query_verb} {phrase1} or {phrase2}."
                         .format(query_verb=random.choice(verbs), phrase1=self.cur_phrases[0],
                                 phrase2=self.cur_phrases[1]))
        self.answers = copy.deepcopy(self.cur_phrases)


    @on_message(r'\.$')
    def on_message(self, event):
        """# we wait for the learner to send a message finalized by a full stop.# if the message sent by the learner
        equals the teacher's selected phrase followed by a period, reward the learner.# If we reached thsi point,
        it fails the task.

        :param event:
        :return:
        """
        for answer in self.answers:
            print(answer)
            if event.is_message_exact(answer, '.'):
                    self.set_result(1, random.choice(msg.congratulations))
                    break
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """# if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """# fail the learnerng a random fail feedback message

        :return:
        """
        self.set_result(0, random.choice(msg.failed))


class RepeatWhatISayConjunctionNegation(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(RepeatWhatISayConjunctionNegation, self).__init__(world=world, max_time=3000)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """# randomly sample two objects# randomly sample existence of negation for first and second object# ask the
        learner to repeat the phrase sampling one of the possible ways of asking that.# compute the answer# generate
        all permutations of objects separated by and# in case of no object (e.g., do not say x and do not say y)
        add space

        :param event:
        :return:
        """
        self.cur_phrases = [random.choice(phrases), random.choice(phrases)]
        self.negation1 = random.choice([0, 1])
        self.negation2 = random.choice([0, 1])
        self.set_message("{negation1} {query_verb} {phrase1} and {negation2} "
                         "{query_verb} {phrase2}."
                         .format(negation1=random.choice(negation)
                             if self.negation1 == 1 else "", query_verb=random.choice(verbs),
                                 phrase1=self.cur_phrases[0], negation2=random.choice(negation)
                             if self.negation2 == 1 else "", phrase2=self.cur_phrases[1]))
        self.answer_parts = []
        if self.negation1 == 1 and self.negation2 == 0 and self.cur_phrases[0] != self.cur_phrases[1]:
            self.answer_parts.append(self.cur_phrases[1])
        else:
            self.answer_parts.append(self.cur_phrases[0])
            if self.negation2 == 0:
                self.answer_parts.append(self.cur_phrases[0])
                self.answer_parts.append(self.cur_phrases[1])
            elif self.cur_phrases[0] != self.cur_phrases[1]:
                    self.answer_parts.append(self.cur_phrases[0])
        self.answers = []
        for answer in itertools.permutations(list(set(self.answer_parts))):
            self.answers.append(" and ".join(answer))
        if not self.answers:
            self.answer.append(" ")


    @on_message(r'\.$')
    def check_response(self, event):
        """ # we wait for the learner to send a message finalized by a full stop.# if the message sent by the
        learner equals the teacher's selected phrase followed by a period, reward the learner. If we reached thsi
        point, it fails the task.

        :param event:
        :return:
        """
        for answer in self.answers:
            if event.is_message_exact(answer, '.'):
                self.set_result(1, random.choice(msg.congratulations))
                break
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        """# if the learner has not produced any plausible answer by the max_time
        # allowed, fail the learner sending appropriate feedback.

        :param event:
        :return:
        """

        self.fail_learner()

    def fail_learner(self):
        """# fail the learner sending a random fail feedback message

        :return:
        """
        self.set_result(0, random.choice(msg.failed))


# timing constants
TIME_CHAR = 8
TIME_VERB = (len("Say 'I xxxxxxxxxxxx' to xxxxxxxxxxxx.") + len("You xxxxxxxxxxxxed.")) * TIME_CHAR


class VerbTask(Task):
    """

    """
    verbs = ('sing', 'smile', 'rest', 'relax', 'jump', 'dance')
    verbs_past = ('sang', 'smiled', 'rested', 'relaxed', 'jumped', 'danced')

    def __init__(self, world):
        """

        :param world:
        """
        super(VerbTask, self).__init__(max_time=2 * TIME_VERB, world=world)

    @on_start()
    def on_start(self, event):
        # TODO event not used
        """

        :param event:
        :return:
        """
        self.target_verb = random.choice(self.verbs)
        self.set_message("Say 'I {0}' to {0}.".format(self.target_verb))

    @on_message(r'\.$')
    def correct(self, event):
        """

        :param event:
        :return:
        """
        if event.is_message(self.target_verb, '.'):
            self.set_result(1, 'You {0}.'.format(
                self.verbs_past[self.verbs.index(self.target_verb)]))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        # TODO event not used
        """

        :param event:
        :return:
        """
        self.fail_learner()

    def fail_learner(self):
        """

        :return:
        """
        self.set_result(0, random.choice(msg.failed))
