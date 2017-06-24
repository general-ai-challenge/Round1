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

import unittest
import core.serializer as serializer
import core.channels as channels


class TestChannels(unittest.TestCase):

    def testInputSerialization(self):
        """

        :return:
        """
        slzr = serializer.StandardSerializer()
        ic = channels.InputChannel(slzr)
        test_string = 'my message'
        serialized_test_string = slzr.to_binary(test_string)

        def all_good(input_message):
            """

            :param input_message:
            :return:
            """
            self.assertEqual(test_string[:len(input_message)], input_message)

        ic.message_updated.register(all_good)
        for b in serialized_test_string:
            ic.consume(b)

    def testInputClear(self):
        """

        :return:
        """
        slzr = serializer.StandardSerializer()
        ic = channels.InputChannel(slzr)
        test_string = 'my message'
        serialized_test_string = slzr.to_binary(test_string)
        for b in serialized_test_string:
            ic.consume(b)

        def all_good(input_message):
            """

            :param input_message:
            :return:
            """
            self.assertEqual('', input_message)

        ic.message_updated.register(all_good)
        ic.clear()

    def testOutputSerialization(self):
        """
        
        :return: 
        """
        slzr = serializer.StandardSerializer()
        oc = channels.OutputChannel(slzr)
        test_string = 'my message'
        serialized_test_string = slzr.to_binary(test_string)
        oc.set_message(test_string)
        for b in serialized_test_string:
            self.assertEqual(b, oc.consume())

    def testConsistency(self):
        """

        :return:
        """
        slzr = serializer.StandardSerializer()
        ic = channels.InputChannel(slzr)
        oc = channels.OutputChannel(slzr)
        test_string = 'my message'

        def all_good(input_message):
            """

            :param input_message:
            :return:
            """
            self.assertEqual(test_string[:len(input_message)], input_message)

        oc.set_message(test_string)
        ic.message_updated.register(all_good)
        while not oc.is_empty():
            b = oc.consume()
            ic.consume(b)

    def testSilenceConsistency(self):
        """

        :return:
        """
        slzr = serializer.StandardSerializer()
        ic = channels.InputChannel(slzr)
        oc = channels.OutputChannel(slzr)
        test_string = slzr.SILENCE_TOKEN * 10
        something_read = [0]

        def all_good(input_message):
            """

            :param input_message:
            :return:
            """
            something_read[0] = len(input_message)
            self.assertEqual(test_string[:len(input_message)], input_message)

        oc.set_message(test_string)
        ic.message_updated.register(all_good)
        while not oc.is_empty():
            b = oc.consume()
            ic.consume(b)
        self.assertEqual(something_read[0], len(test_string))

    def testOverwrittingConsistency(self):
        """ array because Python's scoping rules are demented:
        http://stackoverflow.com/questions/4851463/python-closure-write-to-variable-in-parent-scope

        :return:
        """
        slzr = serializer.StandardSerializer()
        ic = channels.InputChannel(slzr)
        oc = channels.OutputChannel(slzr)
        test_string = 'my message'
        something_read = [0]

        def all_good(input_message):
            """

            :param input_message:
            :return:
            """
            something_read[0] = len(input_message)
            self.assertEqual(test_string[:len(input_message)], input_message)
        oc.set_message("this shouldn't matter")
        oc.set_message(test_string)
        ic.message_updated.register(all_good)
        while not oc.is_empty():
            b = oc.consume()
            ic.consume(b)
        self.assertEqual(something_read[0], len(test_string))

    def testIsSient(self):
        """

        :return:
        """
        slzr = serializer.StandardSerializer()
        oc = channels.OutputChannel(slzr)
        self.assertTrue(oc.is_silent())
        oc.set_message(slzr.SILENCE_TOKEN)
        self.assertTrue(oc.is_silent())
        while not oc.is_empty():
            oc.consume()
            self.assertTrue(oc.is_silent())
        oc.set_message('hello')
        while not oc.is_empty():
            oc.consume()
            if not oc.is_empty():
                self.assertFalse(oc.is_silent())
        self.assertTrue(oc.is_silent())


def main():
    unittest.main()

if __name__ == '__main__':
    main()
