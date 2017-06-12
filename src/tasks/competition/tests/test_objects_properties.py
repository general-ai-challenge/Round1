# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import unittest
import tasks.competition.messages as msg
import tasks.competition.objects_properties as objects_properties
from tasks.competition.tests.helpers import task_messenger
import random

global_properties = objects_properties.global_properties


class TestObjectsProperties(unittest.TestCase):
    """
    helper methods
    """
    def check_positive_feedback(self, m, instructions, answer):
        """ # hear the congratulations # there is some feedback

        :param m:
        :param instructions:
        :param answer:
        :return:
        """
        feedback_blen = m.read()
        self.assertGreater(
            feedback_blen, 0, "answering '{0}' to query '{1}' didn't work.".format(answer, instructions))
        m.send()
        self.assertEqual(
            m.get_cumulative_reward(), 1, "answering '{0}' to query '{1}' didn't work.".format(answer, instructions))

    def check_negative_feedback(self, m, exp_answer):
        """ # hear the feedback # the answer could be a space-separated list that # solves the task in any order
        # exp_answer is not a string and thus, the expected answer is a collection of possibilities

        :param m:
        :param exp_answer:
        :return:
        """
        m.read()
        answer, = m.search_last_message(r"(?:one|the) right \w+ (?:is|are): (.+)\.$")
        m.send()
        try:
            self.assertEqual(set(self.string_to_enum(exp_answer)), set(self.string_to_enum(answer)),
                             "{0} != {1}".format(exp_answer, answer))
        except AttributeError:
            self.assertIn(answer, exp_answer)

    def solve_correctly_test(self, m, get_correct_answer):
        """  read the instructions # get the instructions # get the answer # send the answer with the termination
        marker # hear the congratulations

        :param m:
        :param get_correct_answer:
        :return:
        """
        m.read()
        instructions = m.get_last_message()
        answer = get_correct_answer(m)[0]
        m.send("{0}.".format(answer))
        self.check_positive_feedback(m, instructions, answer)

    def solve_interrupting_teacher(self, m, get_correct_answer):
        """ # read the instructions up to the point we can get the answer # get the answer # borderline condition:
         send the first character and check that the teacher hasn't just stopped talking (if it did, then this would
         be a good response, and it's not what we are testing here) # send the rest of the answer with the termination
         marker # interrupting the teacher shouldn't have worked for us # wait for the teacher to stop talking # get
         the instructions # still no reward  # get the answer now that the teacher is silent # send the answer with
         the termination marker # hear the congratulations

        :param m:
        :param get_correct_answer:
        :return:
        """
        m.read_until(get_correct_answer)
        answer = get_correct_answer(m)[0]
        m.send(answer[0])
        self.assertFalse(m.is_silent(), "failed to interrupt teacher: " "correct answer detected too late.")
        m.send("{0}.".format(answer[1:]))
        self.assertEqual(m.get_cumulative_reward(), 0)
        m.read()
        instructions = m.get_last_message()
        self.assertEqual(m.get_cumulative_reward(), 0)
        answer = get_correct_answer(m)[0]
        m.send("{0}.".format(answer))
        self.check_positive_feedback(m, instructions, answer)

    def timeout_test(self, m, get_correct_answer):
        """ # read the instructions # get the answer # check if the answer is a collection of possibilities or just
        # one option # stay silent # hear the correction

        :param m:
        :param get_correct_answer:
        :return:
        """
        m.read()
        answer = get_correct_answer(m)
        answer = answer[1] if len(answer) > 1 else answer[0]
        while m.is_silent():
            m.send()
        self.check_negative_feedback(m, answer)

    def do_test_battery(self, task, get_correct_answer):
        """ # test for solving the task correctly # test for not solving it at all # test for not solving it at all

        :param task:
        :param get_correct_answer:
        :return:
        """
        with task_messenger(task) as m:
            self.solve_correctly_test(m, get_correct_answer)
        with task_messenger(task) as m:
            self.timeout_test(m, get_correct_answer)
        with task_messenger(task) as m:
            self.solve_interrupting_teacher(m, get_correct_answer)

    separators = [" ", " and ", ", ", ", and "]

    def enum_to_string(self, lst):
        """

        :param lst:
        :return:
        """
        sep = random.choice(self.separators)
        return sep.join(lst)

    def string_to_enum(self, strlst):
        """ # check whether strlst has split (to see if it's a string)

        :param strlst:
        :return:
        """
        splitting = strlst.split
        for sep in sorted(self.separators, key=lambda x: -len(x)):
            if sep in strlst:
                return splitting(sep)
        return [strlst]

"""
    # tasks testing routines
"""
    def testAssociateObjectWithProperty(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            property_, = m.search_last_message(r"basket is (\w+)")
            return property_,

        self.do_test_battery(objects_properties.AssociateObjectWithPropertyTask, get_correct_answer)

    def testVerifyThatObjectHasProperty(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions # send the answer with the termination marker

            :param m:
            :return:
            """
            object_, property_, basket = m.search_last_message(r"(\w+) (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            if property_ in global_properties[basket][object_]:
                answer = "yes"
            else:
                answer = "no"
            return answer,
        self.do_test_battery(objects_properties.VerifyThatObjectHasPropertyTask, get_correct_answer)

    def testListPropertiesOfAnObject(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            object_, basket = m.search_last_message(r"does (\w+) have in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            answer = self.enum_to_string(global_properties[basket][object_])
            return answer,
        self.do_test_battery(objects_properties.ListPropertiesOfAnObjectTask, get_correct_answer)

    def testNameAPropertyOfAnObject(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            object_, basket = m.search_last_message(r"of (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            all_answers = global_properties[basket][object_]
            answer = random.choice(all_answers)
            return answer, all_answers
        self.do_test_battery(objects_properties.NameAPropertyOfAnObjectTask, get_correct_answer)

    def testHowManyPropertiesDoesAnObjectHave(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            object_, basket = m.search_last_message(r"does (\w+) have in (\w+)'s")
            if basket in global_properties and object_ in global_properties[basket]:
                props = global_properties[basket][object_]
                all_answers = [str(len(props))]
                if len(props) <= len(msg.numbers_in_words):
                    all_answers.append(msg.numbers_in_words[len(props)])
            else:
                all_answers = ["0", "zero"]
            answer = random.choice(all_answers)
            return answer, all_answers
        self.do_test_battery(objects_properties.HowManyPropertiesDoesAnObjectHaveTask, get_correct_answer)

    def testListObjectsWithACertainProperty(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            property_, basket = m.search_last_message(r"objects are (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            answer = [object_ for object_ in
                        global_properties[basket]
                        if property_ in
                        global_properties[basket][object_]]
            return " ".join(answer),
        self.do_test_battery(objects_properties.ListObjectsWithACertainPropertyTask, get_correct_answer)

    def testNameAnObjectWithAProperty(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """  # find the answer in the instructions

            :param m:
            :return:
            """
            property_, basket = m.search_last_message(r"is (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            all_answers = [object_ for object_ in
                            global_properties[basket]
                            if property_ in
                            global_properties[basket][object_]]
            answer = random.choice(all_answers)
            self.assertTrue(all_answers, "There are no objects {0} "
                            "in {1}'s basket".format(property_, basket))
            return answer, all_answers
        self.do_test_battery(objects_properties.NameAnObjectWithAPropertyTask, get_correct_answer)

    def testHowManyObjectsHaveACertainProperty(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            property_, basket = m.search_last_message(r"objects are (\w+) in (\w+)'s")
            self.assertIn(basket, global_properties)
            objects = [object_ for object_ in global_properties[basket] if property_ in
                       global_properties[basket][object_]]
            num_objects = len(objects)
            all_answers = [str(num_objects)]
            if num_objects <= len(msg.numbers_in_words):
                all_answers.append(msg.numbers_in_words[num_objects])
            answer = random.choice(all_answers)
            return answer, all_answers
        self.do_test_battery(objects_properties.HowManyObjectsHaveACertainPropertyTask, get_correct_answer)

    def testWhoHasACertainObjectWithACertainProperty(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            property_, object_ = m.search_last_message(r"(\w+) (\w+) in the")
            baskets = [basket for basket, object_props in global_properties.items() if object_ in object_props and
                        property_ in object_props[object_]]
            if not baskets:
                answer = "nobody"
            else:
                answer = " ".join(baskets)
            return answer,
        self.do_test_battery(objects_properties.WhoHasACertainObjectWithACertainPropertyTask, get_correct_answer)

    def testListThePropertiesThatAnObjectHasInABasketOnly(self):
        """

        :param self:
        :return:
        """
        def get_correct_answer(m):
            """ # find the answer in the instructions

            :param m:
            :return:
            """
            object_, basket = m.search_last_message(r"(\w+) have in (\w+)'s")
            self.assertIn(basket, global_properties)
            self.assertIn(object_, global_properties[basket])
            properties = set(global_properties[basket][object_])
            comp_baskets_props = set.union(*[set(object_props[object_])
                    for basket2, object_props in
                    global_properties.items() if basket2 != basket])
            properties_basket_only = properties - comp_baskets_props
            if properties_basket_only:
                answer = " ".join(properties_basket_only)
            else:
                answer = "none"
            return answer,
        self.do_test_battery(objects_properties.ListThePropertiesThatAnObjectHasInABasketOnlyTask, get_correct_answer)

        def testListThePropertiesThatAnObjectHasInAllBaskets(self):
            """

            :param self:
            :return:
            """
            def get_correct_answer(m):
                """ # find the answer in the instructions

                :param m:
                :return:
                """
                object_, = m.search_last_message(r"does (\w+) have")
                all_baskets_props = set.union(*[set(object_props[object_]
                            if object_ in object_props else [])
                        for basket2, object_props in
                        global_properties.items()])
                if all_baskets_props:
                    answer = " ".join(all_baskets_props)
                else:
                    answer = "none"
                return answer,
            self.do_test_battery(objects_properties.ListThePropertiesThatAnObjectHasInAllBasketsTask,
                                 get_correct_answer)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
