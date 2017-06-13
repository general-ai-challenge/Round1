# -*- coding: utf-8
# 'version': '0.2'
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

from core.task import on_start, on_message, on_timeout
from tasks.competition.base import BaseTask
import tasks.competition.messages as msg
import random
import string
import re

# global data structures to be called by multiple tasks

# properties of objects in two baskets, for memory tasks
# (please keep objects in alphabetical order for ease of debugging)
global_properties = {
    'john': {'apple': ['green', 'sour', 'hard', 'cheap', 'healthy', 'juicy', 'local'],
             'banana': ['yellow', 'sweet', 'soft', 'cheap', 'healthy', 'exotic', 'ripe'],
             'beet': ['red', 'dirty', 'hard', 'old', 'cheap', 'sweet', 'healthy', 'local', 'large'],
             'carrot': ['orange', 'hard', 'fresh', 'local', 'healthy', 'sweet', 'crunchy'],
             'cucumber': ['green', 'fresh', 'juicy', 'local', 'cheap', 'healthy', 'frozen', 'crunchy'],
             'mango':  ['brown', 'rotten'],
             'onion': ['white', 'pungent', 'smelly', 'cheap', 'local', 'healthy'],
             'pear': ['brown', 'sweet', 'dry', 'cheap', 'local', 'big'],
             'pineapple': ['yellow', 'sweet', 'hard', 'exotic', 'brown', 'rough'],
             'potato': ['yellow', 'old', 'cheap', 'hard', 'tasteless', 'dirty', 'bumpy'],
             'tomato': ['red', 'soft', 'sour', 'juicy', 'local', 'cheap']},
    'mary': {'apple': ['red', 'sweet', 'hard', 'fresh', 'juicy', 'expensive', 'crunchy'],
             'asparagus': ['white', 'soft', 'old', 'long', 'expensive', 'dirty'],
             'avocado': ['green', 'ripe', 'exotic', 'expensive', 'large', 'healthy', 'smooth', 'buttery'],
             'banana': ['yellow', 'tasteless', 'soft', 'sweet', 'old', 'exotic'],
             'carrot': ['orange', 'hard', 'old', 'dirty', 'local', 'small', 'crunchy'],
             'cucumber': ['green', 'fresh', 'hard', 'cheap', 'local', 'long'],
             'onion': ['yellow', 'old', 'cheap', 'dry', 'local', 'large'],
             'mango': ['red', 'green', 'yellow', 'juicy', 'sweet', 'expensive'],
             'pear': ['green', 'tasteless', 'hard', 'local', 'cheap', 'big'],
             'pineapple': ['yellow', 'sweet', 'dry', 'fresh', 'expensive', 'exotic'],
             'tomato': ['red', 'soft', 'sour', 'local', 'cheap']}}

# it's handy to have a reverse dictionary with the properties in the above lists as keys, and the objects as values
rev_global_properties = {}
for basket in global_properties:
    rev_global_properties[basket] = {}
    for object in global_properties[basket]:
        for property in global_properties[basket][object]:
            if property not in rev_global_properties[basket]:
                rev_global_properties[basket][property] = []
            rev_global_properties[basket][property].append(object)

# create a list of objects
global_objects = []
for p in global_properties:
    for o in global_properties[p]:
        global_objects.append(o)
global_objects = list(set(global_objects))

# a list of questions about a number, shared by multiple tasks
number_questions = ['please tell me the number.',
                    'what\'s the number?',
                    'what is the number?',
                    'can you tell me the number?']

# when an enumeration is given, each element but the last could be followed by: ', ', ' and ', or ', and ' or ' '
delimiters = r'(?:, | and |, and | )'


class ObjectExistenceTask1(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(ObjectExistenceTask1, self).__init__(world=world, max_time=3000)

    @on_start()
    def on_start(self, event):
        """

        :param event:
        :return:
        """
        self.obj = random.choice(global_objects)
        self.obj_question = random.choice(global_objects)
        s = "Let's play game with objects. "
        s += "I have " + self.obj + ". "
        s += "Do I have " + self.obj_question + "?"
        self.set_message(s)

    @on_message("(yes|no).$")
    def on_message(self, event):
        """

        :param event:
        :return:
        """
        if event.is_message("yes", '.'):
            if self.obj == self.obj_question:
                self.set_result(1, "Correct!")
            else:
                s = "Wrong, I do not have " + self.obj_question + ". "
                s += "Do I have " + self.obj_question + "?"
                self.set_message(s)
            return
        if event.is_message("no", '.'):
            if self.obj != self.obj_question:
                self.set_result(1, "Correct!")
            else:
                s = "Wrong, I do have " + self.obj_question + ". "
                s += "Do I have " + self.obj_question + "?"
                self.set_message(s)

    @on_timeout()
    def on_timeout(self, event):
        """

        :param event:
        :return:
        """
        self.set_result(0, "You are too slow! Let's try something else.")


class ObjectExistenceTask2(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(ObjectExistenceTask2, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        """ # pick how many objects in total will be enumerated # for last object change separator from "," to "and"
        # pick object# build up message# update counter# pick object to ask the question
        :param event:
        :return:
        """
        separator = ""
        counter = {}
        message = ""
        total = random.randint(1, 5)
        for i in range(0, total):
            if i == total - 2:
                separator = " and "
            elif i == total - 1:
                separator = ""
            else:
                separator = ", "
            obj = random.choice(global_objects)
            message += msg.indef_article(obj)
            message += separator
            if obj not in counter:
                counter[obj] = 0
            counter[obj] += 1
        object_in_question = random.choice(global_objects)
        self.answer = "Yes" if counter.get(object_in_question, 0) > 0 else "No"
        self.give_away_message = "I do have {object}." if self.answer == "Yes" else "I do not have {object}."
        self.give_away_message = self.give_away_message.format(object=msg.indef_article(object_in_question))
        self.give_away_message = "Wrong. " + self.give_away_message
        self.set_message('I have {listing_objects}. Do I have {object}? '
                            .format(listing_objects=message, object=msg.indef_article(object_in_question)))

    @on_message(r'\.')
    def check_response(self, event):
        """# check if given answer matches# if the message sent by the learner equals the teacher's selected phrase
        followed by a period, reward the learner. # If the learner said anything else, it fails the task.

        :param event:
        :return:
        """
        if event.is_message(self.answer, '.'):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            self.fail_learner()

    @on_timeout()
    def on_timeout(self, event):
        """ if the learner has not produced any plausible answer by the max_time allowed, fail the learner sending
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


class AssociateObjectWithPropertyTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(AssociateObjectWithPropertyTask, self).__init__(world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        """ # pick some random basket, object and property# ask the leearner for the property

        :param event:
        :return:
        """
        basket = random.choice(list(global_properties.keys()))
        object_ = random.choice(list(global_properties[basket].keys()))
        self.property = random.choice(global_properties[basket][object_])
        self.set_message("{object} in {owner}'s basket is {property}. "
                         "how is {object}?".format(object=object_, owner=basket, property=self.property))

    @on_message(r"\.")
    def check_response(self, event):
        """

        :param event:
        :return:
        """
        if event.is_message(self.property, '.'):
            self.set_result(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        """

        :param event:
        :return:
        """
        self.set_message('the right answer is: {answer}.'.format(answer=self.property))


class VerifyThatObjectHasPropertyTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(VerifyThatObjectHasPropertyTask, self).__init__(
            world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        """# extracting the set of properties (from both baskets)# find the properties that that the selected objects
        does NOT have # deciding if we'll ask about the true or false property # ask for a false property # ask for
         a true property

        :param event:
        :return:
        """
        basket = random.choice(list(global_properties.keys()))
        object_ = random.choice(list(global_properties[basket].keys()))
        object_properties = global_properties[basket][object_]
        all_properties = set(property_
                             for temp_basket, object_properties in
                                global_properties.items()
                             for temp_object, temp_properties in
                                object_properties.items()
                             for property_ in temp_properties)

        properties_complement = list(all_properties - set(object_properties))
        self.coin_flip = random.randint(0, 1)
        if not self.coin_flip:
            property_ = random.choice(properties_complement)
            self.answer = "no"
        else:

            property_ = random.choice(object_properties)
            self.answer = "yes"
        self.set_message("is {object} {property} in {owner}'s basket?'"
                         .format(object=object_, property=property_,owner=basket))

    @on_message()
    def check_response(self, event):
        """

        :param event:
        :return:
        """
        if event.is_message(self.answer, '.'):
            self.set_result(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        """

        :param event:
        :return:
        """
        self.set_message('the right answer is: ' + self.answer + '.')


class ListPropertiesOfAnObjectTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(ListPropertiesOfAnObjectTask, self).__init__(world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        """ select a random object from a random basket# retrieving the properties of the selected object# building
        a regexp to match the answer# final string must be delimited by period# add check_response as a handler for
        a message matching the above described enumeration# on_message handler created dynamically when the number of
         expected responses is known

        :param event:
        :return:
        """
        basket = random.choice(list(global_properties.keys()))
        object_ = random.choice(list(global_properties[basket].keys()))

        self.object_properties = set(global_properties[basket][object_])

        self.set_message("which properties does {object} have in "
                         "{owner}'s basket?".format(object=object_, owner=basket))
        enum_re = delimiters.join([r'([a-z]+)'] * len(self.object_properties))
        enum_re += r'\.$'
        self.add_handler(on_message(enum_re)(self.check_response))


    def check_response(self, event):
        """ # get all the elements in the matched enumeration# if the produced elements match the expected properties
        # reward the learner

        :param event:
        :return:
        """
        potential_properties = set(event.get_match_groups())
        if (self.object_properties == potential_properties):
            self.set_result(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        """

        :param event:
        :return:
        """
        correct_properties = list(self.object_properties)
        random.shuffle(correct_properties)
        answer = " ".join(correct_properties)
        self.set_message('the right properties are: {answer}.'.format(answer=answer))


class NameAPropertyOfAnObjectTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(NameAPropertyOfAnObjectTask, self).__init__(world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        """# pick some basket and object# retrieving the properties of the selected object

        :param event:
        :return:
        """
        basket = random.choice(list(global_properties.keys()))
        object_ = random.choice(list(global_properties[basket].keys()))
        self.object_properties = global_properties[basket][object_]
        self.set_message("can you tell me a property of {object} "
                         "in {owner}'s basket?".format(object=object_, owner=basket))

    @on_message()
    def check_response(self, event):
        """# traverse properties list, and see if you find one that is matching

        :param event:
        :return:
        """
        if any(event.is_message(property_, '.')
                for property_ in self.object_properties):
            self.set_result(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        """# randomly picked right property

        :param event:
        :return:
        """
        self.set_message('one right answer is: {answer}.'.format(answer=random.choice(self.object_properties)))


class HowManyPropertiesDoesAnObjectHaveTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(HowManyPropertiesDoesAnObjectHaveTask, self).__init__(world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        """# pick some object in a random basket# counting properties of selected object

        :param event:
        :return:
        """
        basket = random.choice(list(global_properties.keys()))
        object_ = random.choice(list(global_properties[basket].keys()))
        self.property_count = len(global_properties[basket][object_])
        self.set_message("how many property does {object} have "
                         "in {owner}'s basket?".format(object=object_, owner=basket))

    @on_message()
    def check_response(self, event):
        """# check if the answer matches any of the possible ways of expressing the correct number. NB: note that
        here a longer digit string ending with the currect number will be considered correct (e.g., 321 when the
        correct answer is 1)

        :param event:
        :return:
        """
        if any(event.is_message(correct_alt, '.')
               for correct_alt in msg.number_to_strings(self.property_count)):
            self.set_result(1, random.choice(msg.congratulations))

    @on_timeout()
    def give_away_answer(self, event):
        """# inform the answer randomly choosing a numeric or alphabetic format.

        :param event:
        :return:
        """
        self.set_message('the right answer is: {answer}.'.format(answer=msg.number_to_string(self.property_count)))


class ListObjectsWithACertainPropertyTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(ListObjectsWithACertainPropertyTask, self).__init__(world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        """ # chose a random property# retrieving the objects that have this property# building a regexp to match
        the answer# final string must be delimited by period

        :param event:
        :return:
        """
        basket = random.choice(list(rev_global_properties.keys()))
        property_ = random.choice(list(rev_global_properties[basket].keys()))
        self.objects = set(rev_global_properties[basket][property_])
        self.question = "which objects are {property} in {owner}'s basket?".format(property=property_, owner=basket)
        self.set_message(self.question)
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.objects))
        enum_re += r'\.$'
        self.re_query = re.compile(enum_re)


    @on_message(r'\.')
    def check_response(self, event):
        """# on_message handler created dynamically when the number of expected responses is known

        :param event:
        :return:
        """
        re_out=self.re_query.search(event.message)
        if (re_out):
            potential_objects=set(re_out.groups())
        else:
            potential_objects=set()
        if (self.objects == potential_objects):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            answer = self.get_shuffled_correct_objects(self.objects)
            feedback = 'the right objects are: {answer}. please try again. '.format(answer=answer)
            feedback += self.question
            self.set_message(feedback)

    @on_timeout()
    def give_away_answer(self, event):
        """

        :param event:
        :return:
        """
        answer = self.get_shuffled_correct_objects(self.objects)
        self.set_message('you are too slow. the right objects are: {answer}.'.format(answer=answer))

    def get_shuffled_correct_objects(self,ordered_correct_objects):
        """

        :param ordered_correct_objects:
        :return:
        """
        correct_objects = list(ordered_correct_objects)
        random.shuffle(correct_objects)
        return " ".join(correct_objects)


class NameAnObjectWithAPropertyTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(NameAnObjectWithAPropertyTask, self).__init__(world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        """# chose a random property# retrieving the objects that have the selected property

        :param event:
        :return:
        """

        basket = random.choice(list(rev_global_properties.keys()))
        property_ = random.choice(list(rev_global_properties[basket].keys()))
        self.objects = rev_global_properties[basket][property_]
        self.question = "can you tell me an object that is {property} in {owner}'s basket?".format(property=property_,
                             owner=basket)
        self.set_message(self.question)

    @on_message('\.')
    def check_response(self, event):
        """# traverse objects list, and see if you find one that is matching

        :param event:
        :return:
        """

            if any(event.is_message(object_, '.')
                   for object_ in self.objects):
                # is match found, give reward
                self.set_result(1, random.choice(msg.congratulations))
            else:
                feedback = 'one right answer is: {' \
                           'answer}. please try again. '.format(answer=random.choice(self.objects))
                feedback += self.question
                self.set_message(feedback)

    @on_timeout()
    def give_away_answer(self, event):
        """

        :param self:
        :param event:
        :return:
        """
        # randomly random right property
        self.set_message('you are too slow. one right answer is: {answer}.'.format(
            answer=random.choice(self.objects)))


class HowManyObjectsHaveACertainPropertyTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(HowManyObjectsHaveACertainPropertyTask, self).__init__(world=world, max_time=3000)

    @on_start()
    def give_instructions(self, event):
        """# we will sample from the actual properties, plus a random string representing a "property" that no object
        has# added slots to make random properties more likely# if we picked the last integer or higher, we will
        generate a fake property for which the answer should be 0# if instead we picked an integer within the
        property range, let's retrieve the objects and count them

        :param event:
        :return:
        """

        basket = random.choice(list(rev_global_properties.keys()))
        basket_properties = list(rev_global_properties[basket].keys())
        property_pick = random.randint(0, len(basket_properties)+5)
        if property_pick >= len(basket_properties):
            property_ = self.get_random_property(basket_properties)
            self.object_count = 0
        else:
            property_ = basket_properties[property_pick]
            self.object_count = len(rev_global_properties[basket][property_])
        self.question = "how many objects are {property} in {owner}'s basket?".format(property=property_, owner=basket)
        self.set_message(self.question)

    def get_random_property(self, basket_properties):
        """ # return a random property that is not in basket_properties# generate random property # make sure this
        is not, by chance, identical to a real property in the relevant basket

        :param basket_properties:
        :return:
        """
        while True:
            property_ = "".join(random.sample(string.ascii_lowercase, random.randint(1, 10)))
            if property_ not in basket_properties:
                break
        return property_

    @on_message('\.')
    def check_response(self, event):
        """ check if the answer matches any of the possible ways of expressing the correct number. NB: note that
        here a longer digit string ending with the currect number will be considered correct (e.g., 321 when the
        correct answer is 1)

        :param event:
        :return:
        """
        if any(event.is_message(correct_alt, '.')
               for correct_alt in msg.number_to_strings(self.object_count)):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            feedback = 'the right answer is: {' 'answer}. please try again. '.format(
                answer=msg.number_to_string(self.object_count))
            feedback += self.question
            self.set_message(feedback)

    @on_timeout()
    def give_away_answer(self, event):
        """# inform the answer randomly choosing a numeric or alphabetic format.

        :param event:
        :return:
        """

        self.set_message('you are too slow. the right answer is: {answer}.'.format(
            answer=msg.number_to_string(self.object_count)))


class WhoHasACertainObjectWithACertainPropertyTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(WhoHasACertainObjectWithACertainPropertyTask, self).__init__(world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        """# we find the set of baskets that have the relevant object and property combination# at this point, if
        baskets list is empty we add "nobody" as the only item in it # building a regexp to match the answer#
        final string must be delimited by period

        :param event:
        :return:
        """
        object_, property_ = self.get_random_object_property()
        self.basket_set = set(basket for basket, object_properties
                                in global_properties.items()
                                if object_ in object_properties and property_ in object_properties[object_])
        if not self.basket_set:
            self.basket_set.add('nobody')
        self.question = "who has {property_object} in the basket?".format(
            property_object=msg.indef_article(property_ + " " + object_))
        self.set_message(self.question)
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.basket_set))
        enum_re += r'\.$'
        self.re_query = re.compile(enum_re)

    def get_random_object_property(self):
        """# we traverse the baskets building sets of all the objects and properties they contain as well as
        dictionary of sets recording the object+property pairs present in each basket# now we build a random
        object+property combination from the sets of objects and properties in both baskets

        :return:
        """
        objects_set = set([object_
                           for basket, object_properties
                           in global_properties.items()
                           for object_ in object_properties])
        properties_set = set([property_
                              for basket, property_objects
                              in rev_global_properties.items()
                              for property_ in property_objects])
        object_ = random.choice(list(objects_set))
        property_ = random.choice(list(properties_set))
        return object_, property_

    @on_message(r'\.')
    def check_response(self, event):
        """

        :param event:
        :return:
        """
        re_out=self.re_query.search(event.message)
        if (re_out):
            potential_baskets=set(re_out.groups())
        else:
            potential_baskets=set()
        if (self.basket_set == potential_baskets):
            self.set_result(1, random.choice(msg.congratulations))
        else:
            answer = self.get_shuffled_correct_baskets(self.basket_set)
            feedback = 'the right answer is: {answer}. please try again. '.format(answer=answer)
            feedback += self.question
            self.set_message(feedback)

    @on_timeout()
    def give_away_answer(self, event):
        """

        :param event:
        :return:
        """
        answer = self.get_shuffled_correct_baskets(self.basket_set)
        self.set_message('you are too slow. the right answer is: {answer}.'.format(answer=answer))

    def get_shuffled_correct_baskets(self,ordered_correct_baskets):
        """

        :param ordered_correct_baskets:
        :return:
        """
        correct_baskets = list(ordered_correct_baskets)
        random.shuffle(correct_baskets)
        return " ".join(correct_baskets)


class ListThePropertiesThatAnObjectHasInABasketOnlyTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(ListThePropertiesThatAnObjectHasInABasketOnlyTask, self).__init__(world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        """# get an object that appears in a least two baskets # choose one of the baskets # ask the learner
        # construct the expected answer which is given by the properties of the object in the given basket minus
         t he properties in all the rest of the baskets:# building a regexp to match the answer# final string must
         be delimited by period

        :param event:
        :return:
        """

        object_, object_baskets = self.get_object_in_many_baskets()

        basket = random.choice(object_baskets)

        self.question = "which properties does {" \
                        "object} have in {owner}'s basket only?".format(object=object_, owner=basket)
        self.set_message(self.question)
        self.distinctive_properties_set = self.get_expected_answer(object_, basket, object_baskets)
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.distinctive_properties_set))
        enum_re += r'\.$'
        self.re_query = re.compile(enum_re)

    def get_expected_answer(self, object_, basket, object_baskets):
        """# get the properties for the object in the chosen basket# get the list of properties that the object has
        in the given basket but not in the others. we finally the set of properties that the object only has in
        # the selected basket# if distinctive properties set is empty we add "none" as
        # the only item in it

        :param object_:
        :param basket:
        :param object_baskets:
        :return:
        """
        properties_in_basket = set(global_properties[basket][object_])
        properties_in_other_baskets = set(
            prop for other_basket in object_baskets for prop in global_properties[other_basket][object_]
            if other_basket != basket)
        distinctive_properties_set = properties_in_basket - properties_in_other_baskets
        if not distinctive_properties_set:
            distinctive_properties_set.add('none')
        return distinctive_properties_set

    def get_object_in_many_baskets(self):
        """# we traverse the baskets recording, for each object, the baskets it is in traverse baskets_with_object,
        keeping track of those objects that occur in more than one basket (otherwise the "only"question does not
        make sense due to a presuppostion violation)# now we pick a random object from this list# return the object
        together with the baskets where it occurs

        :return:
        """
        baskets_with_object = {}
        for basket in global_properties:
            for obj in global_properties[basket]:
                if obj not in baskets_with_object:
                    baskets_with_object[obj] = []
                baskets_with_object[obj].append(basket)
        legit_objects = [obj for obj, baskets in baskets_with_object.items()
                             if len(baskets) > 1]
        object_ = random.choice(legit_objects)
        return object_, baskets_with_object[object_]

    @on_message('\.')
    def check_response(self, event):
        """

        :param event:
        :return:
        """
        re_out=self.re_query.search(event.message)
        if (re_out):
            potential_properties=set(re_out.groups())
        else:
            potential_properties=set()
        if self.distinctive_properties_set == potential_properties:
            self.set_result(1, random.choice(msg.congratulations))
        else:
            answer = self.get_shuffled_correct_properties(self.distinctive_properties_set)
            feedback = 'the right properties are: {answer}. please try again. '.format(answer=answer)
            feedback += self.question
            self.set_message(feedback)

    @on_timeout()
    def give_away_answer(self, event):
        """

        :param event:
        :return:
        """
        answer = self.get_shuffled_correct_properties(self.distinctive_properties_set)
        self.set_message('you are too slow. the right properties are: {answer}.'.format(answer=answer))

    def get_shuffled_correct_properties(self,ordered_correct_properties):
        """

        :param ordered_correct_properties:
        :return:
        """
        correct_properties = list(ordered_correct_properties)
        random.shuffle(correct_properties)
        return " ".join(correct_properties)


class ListThePropertiesThatAnObjectHasInAllBasketsTask(BaseTask):
    """

    """
    def __init__(self, world=None):
        """

        :param world:
        """
        super(ListThePropertiesThatAnObjectHasInAllBasketsTask, self).__init__(
            world=world, max_time=3500)

    @on_start()
    def give_instructions(self, event):
        """ # get an object that appears in a least two baskets# ask the learner# construct the expected answer
        which is given by the properties of the object in the given basket minus the properties in all the rest of
        the baskets:# building a regexp to match the answer# final string must be delimited by period

        :param event:
        :return:
        """
        object_, object_baskets = self.get_object_in_many_baskets()
        self.question = "which properties does {object} have in all baskets?".format(object=object_)
        self.set_message(self.question)
        self.shared_properties_set = self.get_expected_answer(object_, object_baskets)
        enum_re = delimiters.join(
            [r'([a-z]+)'] * len(self.shared_properties_set))
        enum_re += r'\.$'
        self.re_query = re.compile(enum_re)

    def get_expected_answer(self, object_, object_baskets):
        """# get the properties that are present in all the baskets for the selected object# if set is empty,
         we put 'none' in it

        :param object_:
        :param object_baskets:
        :return:
        """
        shared_properties_set = set.intersection(*[set(prop for prop in global_properties[basket][object_])
            for basket in object_baskets])
        if len(shared_properties_set) == 0:
            shared_properties_set.add('none')
        return shared_properties_set

    def get_object_in_many_baskets(self):
        """# we traverse the baskets recording, for each object, the baskets it is in# traverse baskets_with_object,
        keeping track of those objects that occur in more than one basket (otherwise the "only" question does not
        make sense due to a presuppostion violation)# now we pick a random object from this list# return the object
        together with the baskets where it occurs

        :return:
        """
        baskets_with_object = {}
        for basket in global_properties:
            for obj in global_properties[basket]:
                if obj not in baskets_with_object:
                    baskets_with_object[obj] = []
                baskets_with_object[obj].append(basket)
        legit_objects = [obj for obj, baskets in baskets_with_object.items()
                             if len(baskets) > 1]
        object_ = random.choice(legit_objects)
        return object_, baskets_with_object[object_]

    @on_message('\.')
    def check_response(self, event):
        """

        :param event:
        :return:
        """
        re_out=self.re_query.search(event.message)
        if (re_out):
            potential_properties=set(re_out.groups())
        else:
            potential_properties=set()
        if self.shared_properties_set == potential_properties:
            self.set_result(1, random.choice(msg.congratulations))
        else:
            answer = self.get_shuffled_correct_properties(self.shared_properties_set)
            feedback = 'the right properties are: {answer}. please try again. '.format(answer=answer)
            feedback += self.question
            self.set_message(feedback)


    @on_timeout()
    def give_away_answer(self, event):
        """

        :param event:
        :return:
        """
        answer = self.get_shuffled_correct_properties(self.shared_properties_set)
        self.set_message('you are too slow. the right properties are: {answer}.'.format(answer=answer))

    def get_shuffled_correct_properties(self,ordered_correct_properties):
        """

        :param ordered_correct_properties:
        :return:
        """
        correct_properties = list(ordered_correct_properties)
        random.shuffle(correct_properties)
        return " ".join(correct_properties)
