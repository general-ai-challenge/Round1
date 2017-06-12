# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import random

"""# a list of congratulations messages to be issued when the learner solves a task# a list of congratulations 
messages to be issued when the learner fails a task# handy list with word transcriptions of the integers from 0 to 10
"""
congratulations = ['good job.', 'bravo.', 'congratulations.', 'nice work.', 'correct.']
failed = ['wrong!', 'wrong.', 'you failed!', 'incorrect.']
timeout = ['time is out!', 'sorry, time is out!', 'too bad, time out!']
numbers_in_words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']


def number_to_string(num):
    """Returns a string version of a number, randomly picking between letters and numbers.

    :param num:
    :return:
    """
    return random.choice(number_to_strings(num))

def number_to_strings(num):
    """ Returns all the string versions of a number.

    :param num:
    :return:
    """
    ret = [str(num)]
    if num <= len(numbers_in_words):
        ret.append(numbers_in_words[num])
    return ret


def string_to_number(n):
    """

    :param n:
    :return:
    """
    if n in numbers_in_words:
        return numbers_in_words.index(n)
    else:
        return int(n)

"""
# simple grammatical functions
"""

def indef_article(x):
    """

    :param x:
    :return:
    """
    if x[0] in 'aeiou':
        return 'an ' + x
    else:
        return 'a ' + x


def pluralize(obj, c):
    """

    :param obj:
    :param c:
    :return:
    """
    if c == 1:
        return obj
    else:
        return obj + 's'


def lemmatize(word):
    """ if the word ends with an s and it's the result of pluralization remove the s:

    :param word:
    :return:
    """
    if word[-1] == 's' and pluralize(word[:-1], 2) == word:
        return word[:-1]
    else:
        return word
