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

        return nfa, final_state_ngram_length # final_state_ngram_length dictionary will be useful for accepting/rejecting

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

        return ret

    def get_correct_string(self):
        return ''

    def get_wrong_string(self, randomization=1.0):
        return ''

    def _eval_positive(self, string):
        """Verify if the positive NFA recognises given word.

        :param str string: word to be recognised
        :rtype: bool"""

        require_all = self.logical_op == "and"
        if require_all:
            missingFinalStates = set(self.positive_automaton.Final)

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
                        missingFinalStates.discard(f)
                    if last_confirmed + self._final_state_ngram_length[f] >= i : # > condition is true if there's more than one match
                        last_confirmed = i # there is no unmatched character in word up to position i
        if last_confirmed+1 != len(string): # there is an unmatched character at position last_confirmed + 1
            return False
        if(require_all and len(missingFinalStates) != 0):
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
            ilist = automaton.evalSymbol(ilist, string[i]).union(ilist)
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
    return DummyAutomatonInterface(description, logical_op)


obj = build_automaton("GLE EB CDX","or");
print(obj.is_string_correct("GLEB"))
print(obj)