from FAdo.fa import *
import math


class MiniTasksAutomatonInterface():

    _separator_string = " "
    _negation_string = "not"
    _anything_string = "anything"
    _and_string = "and"
    _or_string = "or"
    _sigma = []
    for i in range(26):
        _sigma.append(chr(ord('A') + i))

    def __init__(self, description, logical_op):
        self.description = description
        self.description_split = self.description.split(self._separator_string)
        self.logical_op = logical_op
        self.positive_table = self._parse_positive_from_description()
        self.negative_table = self._parse_negative_from_description()
        self.anything_allowed = self._parse_anything_from_description()
        self.positive_automaton, self._final_state_ngram_length = self._build_automaton(self.positive_table)
        self.negative_automaton, dummy = self._build_automaton(self.negative_table)

    def _build_automaton(self, ngram_table):
        nfa = NFA()
        final_state_ngram_length = {}

        nfa.setSigma(self._sigma)
        initial_state = 0
        nfa.addState(initial_state)
        nfa.addInitial(initial_state)
        state = 1

        for string in ngram_table:
            source_state = initial_state

            for i in range(len(string)):
                # loop on initial state is added during usage of the automaton to increase efficiency
                nfa.addState(state)
                nfa.addTransition(source_state, string[i], state)
                if i == len(string) - 1:
                    nfa.addFinal(state)
                    nfa.addTransition(state, '@epsilon', initial_state) # epsilon-transition
                    final_state_ngram_length[state] = len(string)
                source_state = state
                state += 1

        return nfa, final_state_ngram_length # final_state_ngram_length dictionary will be useful for accepting

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
            if string != self._anything_string:
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
                if string != self._anything_string:
                    ret.append(string)

        return ret

    def _parse_anything_from_description(self):

        for string in self.description_split:
            if string == self._anything_string:
                return True

        return False

    def get_correct_string(self):
        return ''

    def _get_random_string(self, length):
        chrlist = [chr(ord('A')+int(math.floor(random.random()*26))) for i in range(length)]
        return "".join(chrlist)

    def _get_random_wrong_string(self):
        for i in range(100):
            string_length = int(math.ceil(random.random()*20))
            str = self._get_random_string(string_length)
            if not self.is_string_correct(str):
                return str
        raise AssertionError("could not generate a random string that would not be accepted by the automaton")


    def get_wrong_string(self, randomization=1.0):
        str = self._get_random_wrong_string()
        return str

    def _eval_positive(self, string):
        """Verify if the positive NFA recognises given word.

        :param str string: word to be recognised
        :rtype: bool"""

        require_all = self.logical_op == self._and_string
        if require_all:
            missing_final_states = set(self.positive_automaton.Final)

        automaton = self.positive_automaton
        ilist = automaton.epsilonClosure(automaton.Initial)
        initial = ilist.copy()
        last_confirmed = -1

        for i in range(len(string)):
            ilist = automaton.evalSymbol(ilist, string[i]).union(initial)
            if not ilist:
                return False
            for f in automaton.Final:
                if f in ilist:
                    if require_all:
                        missing_final_states.discard(f)
                    if last_confirmed + self._final_state_ngram_length[f] >= i :
                        # > condition is true if there's more than one match
                        last_confirmed = i # there is no unmatched character in word up to position i

        if last_confirmed+1 != len(string) and not self.anything_allowed:
            # there is an unmatched character at position last_confirmed + 1
            return False

        if require_all and len(missing_final_states) != 0:
            return False

        return True

    def _eval_negative(self, string):
        """Verify if the negative NFA matches any ngram in the given word.

        :param str string: string to be recognised
        :rtype: bool"""

        automaton = self.negative_automaton
        ilist = automaton.epsilonClosure(automaton.Initial)
        initial = ilist.copy()

        for i in range(len(string)):
            ilist = automaton.evalSymbol(ilist, string[i]).union(initial)
            for f in automaton.Final:
                if f in ilist:
                    return True # a single match is enough
        return False

    def is_string_correct(self, string):
        pos = self._eval_positive(string)
        if not pos:
            return False

        neg = self._eval_negative(string)
        if neg:
            return False

        return True


def build_automaton(description, logical_op):
    return MiniTasksAutomatonInterface(description, logical_op)
