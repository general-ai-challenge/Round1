from FAdo.fa import *

class DummyAutomatonInterface():

    _negation_string = "not"
    _sigma = []
    for i in range(26):
        _sigma.append(chr(ord('A') + i))

    def __init__(self, description, logical_op):
        self.description = description
        self.description_split = self.description.split(' ')
        self.logical_op = logical_op
        self.positive_table = self._parse_positive_from_description()
        self.negative_table = self._parse_negative_from_description()
        self.automaton = self._build_automaton()

    def _build_automaton(self):
        ret = NFA()
        ret.setSigma(self._sigma)
        initial_state = 0
        ret.addState(initial_state)
        ret.addInitial(initial_state)
        state = 1

        # positive table first
        for string in self.positive_table:
            source_state = initial_state

            for i in range(len(string)):
                ret.addState(state)
                ret.addTransition(source_state, string[i], state)
                if i == len(string) - 1:
                    ret.addFinal(state)
                    ret.addTransition(state, '@epsilon', initial_state) # epsilon-transition
                source_state = state
                state += 1

        return ret

    def _parse_positive_from_description(self):
        ret = []
        next_negated = False

        for string in self.description_split:
            if len(string) == 0:
                continue
            if next_negated :
                next_negated = False
                continue
            if string == self._negation_string:
                next_negated = True
                continue
            ret.append(string)

        return ret

    def _parse_negative_from_description(self):
        ret = []
        next_negated = False

        for string in self.description_split:
            if len(string) == 0:
                continue
            if string == self._negation_string:
                next_negated = True
                continue
            if next_negated:
                next_negated = False
                ret.append(string)
                continue

        return ret

    def get_correct_string(self):
        return ''

    def get_wrong_string(self, randomization=1.0):
        return ''

    def is_string_correct(self, string):
        return self.automaton.evalWordP(string)


def build_automaton(description, logical_op):
    return DummyAutomatonInterface(description, logical_op)


