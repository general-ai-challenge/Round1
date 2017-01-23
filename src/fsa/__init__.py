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
        self.positive_automaton, self.positive_state_depth_dict = self._build_automaton(self.positive_table)
        self.negative_automaton, self.negative_state_depth_dict = self._build_automaton(self.negative_table)

    def _is_in_final_state(self, automaton, state):
        for f in automaton.Final:
            if f in state:
                return True
        return False

    def _build_automaton(self, ngram_table):
        nfa = NFA()

        nfa.setSigma(self._sigma)
        initial_state = 0
        state_depth_dict = {initial_state: 0}
        nfa.addState(initial_state)
        nfa.addInitial(initial_state)
        state = 1

        for string in ngram_table:
            source_state = initial_state

            for i in range(len(string)):
                # loop on initial state is added during usage of the automaton to increase efficiency
                nfa.addState(state)
                nfa.addTransition(source_state, string[i], state)
                state_depth_dict[state] = i + 1
                if i == len(string) - 1:
                    nfa.addFinal(state)
                    nfa.addTransition(state, '@epsilon', initial_state)  # epsilon-transition
                source_state = state
                state += 1

        return nfa, state_depth_dict # final_state_ngram_length dictionary will be useful for accepting

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

    def _get_available_transition_symbols(self, automaton, state_depth_dict, from_states, min_depth):
        # assumes epsilon-closure has been performed on the from_states
        # assumes a trie-like structure of states with epsilon transition from final states to the initial state
        assert(len(from_states) != 0)
        symbols = set()
        for state in from_states:
            if state_depth_dict[state] < min_depth:
                continue
            transition = automaton.delta[state]
            assert len(transition) > 0
            for symbol in transition:
                if symbol == '@epsilon':
                    continue # assumes epsilon transitions occur only from final states to initial state
                symbols.add(symbol)  # assumes the target state has a greater depth than the source state

        return symbols

    def get_correct_string(self):
        # positive automaton part first
        current = last_confirmed = -1
        automaton = self.positive_automaton
        state = automaton.epsilonClosure(automaton.Initial)
        initial = state.copy()
        missing_states = automaton.Final.copy()
        threshold_length = int(math.ceil(random.random()*20))  # strings longer than 20 characters are not necessary now
        chrs = []
        attractor_state = None

        while True:
            symbols = self._get_available_transition_symbols(automaton, self.positive_state_depth_dict, state,
                                                             current - last_confirmed)
            next_symbol = None
            pick_next_symbol_randomly = True

            if current >= threshold_length:

                if len(missing_states) > 0 and self.logical_op == self._and_string:
                    if attractor_state not in missing_states:
                        attractor_state = random.sample(missing_states, 1)[0]
                    attractor_state_depth = self.positive_state_depth_dict[attractor_state]
                    to_try = list(range(attractor_state - attractor_state_depth+1, attractor_state+1))
                    to_try.reverse()

                    # try to reach missing states when in "and" mode
                    # find a symbol that will lead to one of the missing states (if there is such a symbol)
                    for possible_target in to_try:
                        did_break = False
                        for symbol in symbols:
                            target = automaton.evalSymbol(state, symbol)
                            if possible_target in target:
                                state = target
                                next_symbol = symbol
                                pick_next_symbol_randomly = False
                                did_break = True
                                break
                        if did_break:
                            break

                else:
                    if self._is_in_final_state(automaton,state):
                        break

            if pick_next_symbol_randomly:
                next_symbol = random.sample(symbols, 1)[0]
                state = automaton.evalSymbol(state, next_symbol).union(initial)

            missing_states = missing_states.difference(state)
            current+=1
            chrs.append(next_symbol)
            if self._is_in_final_state(automaton,state):
                last_confirmed = current

        str = ''.join(chrs)
        assert(self.is_string_correct(str))
        return str

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
            ilist = automaton.evalSymbol(ilist, string[i]).union(initial)  # loop here to be a matcher automaton
            if not ilist:
                return False
            for f in automaton.Final:
                if f in ilist:
                    if require_all:
                        missing_final_states.discard(f)
                    if last_confirmed + self.positive_state_depth_dict[f] >= i:
                        # > condition is true if there's more than one match
                        last_confirmed = i  # there is no unmatched character in word up to position i

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
            ilist = automaton.evalSymbol(ilist, string[i]).union(initial) # loop here to be a matcher automaton
            if self._is_in_final_state(automaton, ilist):
                return True  # a single match is enough
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
