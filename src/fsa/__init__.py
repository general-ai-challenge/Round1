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
        assert((len(self.negative_table) == 0) or self.anything_allowed)  # "not" occurs => self.anything_allowed
        self.positive_automaton, self.positive_state_depth_dict, self.positive_alphabet = self._build_automaton(self.positive_table)
        self.negative_automaton, self.negative_state_depth_dict, self.negative_alphabet = self._build_automaton(self.negative_table)
        self._distribute_remaining_alphabet_symbols()

    def _distribute_remaining_alphabet_symbols(self):
        """
        takes unused alphabet symbols and distributes them randomly between the positive and negative alphabets
        :return: None
        """
        if len(self.negative_alphabet) == 0:
            self.positive_alphabet = list(self._sigma)
            return

        all = set(self._sigma)
        all.difference_update(set(self.positive_alphabet))
        all.difference_update(self.negative_alphabet)
        for symbol in all:
            if random.random() > 0.5:
                self.positive_alphabet.append(symbol)
            else:
                self.negative_alphabet.append(symbol)
        return

    def _is_in_final_state(self, automaton, state):
        for f in automaton.Final:
            if f in state:
                return True
        return False

    def _build_automaton(self, ngram_table):
        """
        # builds a trie-like automaton without any loops
        :param ngram_table: the ngrams which will form the trie
        :return: automaton, association table from state to its distance from initial state, alphabet of the n-grams
        """
        nfa = NFA()

        nfa.setSigma(self._sigma)
        initial_state = 0
        state_depth_dict = {initial_state: 0}
        nfa.addState(initial_state)
        nfa.addInitial(initial_state)
        state = 1
        alphabet = []

        for string in ngram_table:
            source_state = initial_state

            for i in range(len(string)):
                # loop on initial state is added during usage of the automaton to increase efficiency
                nfa.addState(state)
                nfa.addTransition(source_state, string[i], state)
                alphabet.append(string[i])
                state_depth_dict[state] = i + 1
                if i == len(string) - 1:
                    nfa.addFinal(state)
                source_state = state
                state += 1

        return nfa, state_depth_dict, alphabet  # state_depth_dict will be useful for accepting

    def _parse_positive_from_description(self):
        """
        Get the list of n-grams that are not negated (and not "anything") in the input string
        :return: the list
        """
        ret = []
        next_negated = False

        for string in self.description_split:
            if len(string) == 0:
                continue
            if next_negated:
                next_negated = False
                continue
            if string == self._negation_string:
                next_negated = True
                continue
            if string != self._anything_string:
                ret.append(string)

        return ret

    def _parse_negative_from_description(self):
        """
        Get the list of n-grams that are negated (and not "anything") in the input string
        :return: the list
        """
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
        """
        Find out if there's an "anything" string in the input
        :return: true/false
        """
        for string in self.description_split:
            if string == self._anything_string:
                return True

        return False

    def _get_available_transition_symbols(self, automaton, state_depth_dict, from_states, min_depth):
        """
        computes which symbols are available for making a transition if the reachable states are at least of min_depth
        assumes epsilon-closure has been performed on the from_states
        assumes a trie-like structure of states
        :param automaton:
        :param state_depth_dict:
        :param from_states:
        :param min_depth:
        :return: the set of symbols
        """
        assert(len(from_states) != 0)
        symbols = set()
        for state in from_states:
            if state_depth_dict[state] < min_depth:
                continue
            if state not in automaton.delta:
                continue
            transition = automaton.delta[state]
            assert len(transition) > 0
            for symbol in transition:
                symbols.add(symbol)  # assumes the target state has a greater depth than the source state

        return symbols

    def _get_correct_not_string(self, length, current_chrs):
        """
        this function simulates a negative automaton (automaton for not strings) and if it should make
        a transition to a final state, it does not take it and chooses a different symbol. This function
        would fail if all symbols for the negative alphabet led to a final state, but that is not likely to happen
        given that the negative alphabet is split 50/50 with the positive alphabet

        :param length: the length of the string to generate
        :param current_chrs: the string that was generated so far
        :return:
        """
        chrs = []
        automaton = self.negative_automaton
        state = automaton.epsilonClosure(automaton.Initial)
        initial = state.copy()

        # to avoid a bug that it puts two almost not strings together to form a full not string
        for c in current_chrs:
            state = automaton.evalSymbol(state, c).union(initial)

        alphabet_to_use = self.negative_alphabet

        for pos in range(length):
            random.shuffle(alphabet_to_use)
            for symbol in alphabet_to_use:
                try_state = automaton.evalSymbol(state, symbol)
                if not self._is_in_final_state(automaton, try_state):
                    state = try_state.union(initial)  # loop to be a matcher automaton
                    chrs.append(symbol)
                    break

        return chrs

    def _get_correct_anything_string(self, length, state):
        """
        This function generates a string from the positive alphabet that is not matched by any n-gram
        from the positive table. Moreover, the string, concatenated with the characters generated so far,
        must not create a match - therefore there is the 'state' parameter to help

        notice that the implementation is similar to _get_correct_not_string
        :param length: the length of the string to generate
        :param state: the current state that the positive automaton is in
        :return:
        """
        chrs = []
        automaton = self.positive_automaton
        initial = automaton.epsilonClosure(automaton.Initial)

        alphabet_to_use = self.positive_alphabet

        for pos in range(length):
            random.shuffle(alphabet_to_use)
            for symbol in alphabet_to_use:
                try_state = automaton.evalSymbol(state, symbol)
                if not self._is_in_final_state(automaton, try_state):
                    state = try_state.union(initial)  # loop to be a matcher automaton
                    chrs.append(symbol)
                    break

        return chrs, state

    def get_correct_string(self, length):
        """
        Generate a string accepted by the automaton
        :return: the generated string
        """
        return self._get_string(length, True)

    def _find_symbol_which_leads_to_earliest_state(self, automaton, state, symbols, states_to_try):
        for possible_state in states_to_try:
            for symbol in symbols:
                target = automaton.evalSymbol(state, symbol)
                if possible_state in target:
                    return symbol
        return None

    def _get_string(self, threshold_length, make_correct=True, avoid_states=None, insert_not_string=None):
        """
        Generate a string that is either accepted (make_correct == True) or not accepted (make_correct == False) by
        the function is_string_correct().
        :param threshold_length: Approximate length of the string
        :param make_correct: Whether to generate the accepted or rejected string
        :param avoid_states: Which final states never to visit during generating (useful for rejected strings)
        :param insert_not_string: Whether to insert a string that is forbidden in accepted strings
        :return: the generated string
        """
        current = last_confirmed = -1  # the symbols get confirmed up to current when a final state is visited
        automaton = self.positive_automaton
        state = automaton.epsilonClosure(automaton.Initial)
        initial = state.copy()
        missing_states = automaton.Final.copy()  # when doing "and" generation, all final states must be visited
        chrs = []  # will hold the generated string
        attractor_state = None  # useful when doing "and" generation and we want to force visiting certain final state

        while True:  # until the string is generated
            if last_confirmed == current and \
                    self.anything_allowed:  # insert an "anything" string into the generated string
                # (last_confirmed == current) is true after a final state is entered
                # when "not" strings are used, there's always "anything" allowed (asserted above)
                if random.random() > 0.5:
                    # random: do not insert the "anything" strings always
                    if random.random() > 0.5 or len(self.negative_table) == 0:
                        newchrs, state = self._get_correct_anything_string(int(math.ceil(random.random() * 5)), state)
                    else:
                        newchrs = self._get_correct_not_string(int(math.ceil(random.random() * 5)), chrs)
                        state = initial.copy()
                    current = last_confirmed = current + len(newchrs)
                    chrs.extend(newchrs)

            if len(self.positive_table) > 0:
                symbols = self._get_available_transition_symbols(automaton, self.positive_state_depth_dict, state,
                                                                 current - last_confirmed)

                next_symbol = None
                pick_next_symbol_randomly = True

                if current >= threshold_length:
                    if not make_correct:
                        break
                    if len(missing_states) > 0 and self.logical_op == self._and_string:
                        # when finishing generating the "and" strings, force-visit the missing final states
                        if attractor_state not in missing_states:
                            attractor_state = random.sample(missing_states, 1)[0]
                        attractor_state_depth = self.positive_state_depth_dict[attractor_state]
                        # the states that correspond to one n-gram form a sequence:
                        states_to_try = list(range(attractor_state - attractor_state_depth + 1, attractor_state + 1))
                        states_to_try.reverse()
                        # try to reach missing states when in "and" mode
                        # find a symbol that will lead to one of the missing states (if there is such a symbol)
                        found_symbol = self._find_symbol_which_leads_to_earliest_state(automaton, state,
                                                                                       symbols, states_to_try)
                        if found_symbol is not None:
                            next_symbol = found_symbol
                            pick_next_symbol_randomly = False

                    else:
                        if self._is_in_final_state(automaton, state):
                            # finish generating only after generating the rest of the last n-gram
                            break

                confirm_last_pick = False

                if pick_next_symbol_randomly:
                    if make_correct or len(avoid_states) == 0:  # free to pick any from the available symbols
                        assert(len(symbols) > 0)
                        next_symbol = random.sample(symbols, 1)[0]

                    else:  # generate a symbol that will not lead to one of the states in avoid_states
                        found_symbol = False
                        symbol_list = list(symbols)
                        random.shuffle(symbol_list)
                        for symbol in symbol_list:
                            try_state = automaton.evalSymbol(state, symbol)
                            if len(try_state.intersection(avoid_states)) == 0:
                                next_symbol = symbol
                                found_symbol = True
                            else:  # there is an intersection: we need to avoid this (final) state
                                confirm_last_pick = True  # we're avoiding a final state: pretend there was a match

                        if not found_symbol or random.random() > 0.9:  # pick a random symbol not in "symbols" as next
                            next_symbol = random.sample(set(self._sigma).difference(symbols), 1)[0]
                            confirm_last_pick = True

                state = automaton.evalSymbol(state, next_symbol).union(initial)
                missing_states = missing_states.difference(state)
                chrs.append(next_symbol)
                if self._is_in_final_state(automaton, state):
                    confirm_last_pick = True

                current += 1
                if confirm_last_pick:
                    last_confirmed = current
            else:
                if current >= threshold_length:
                    break

        # insert a string from the "not" table
        if not make_correct and insert_not_string is not None:
            randSplit = int(math.floor(random.random() * len(chrs)))
            chrsA = chrs[:randSplit]
            chrsB = chrs[randSplit:]
            chrsA.extend(list(insert_not_string))
            chrsA.extend(chrsB)
            chrs = chrsA

        str = ''.join(chrs)

        # debug info:
        if not self.is_string_correct(str) == make_correct:
            print(str)
            print(self.description)
            print(self.logical_op)
            assert(self.is_string_correct(str) == make_correct)

        return str

    def _get_random_string(self, length):
        """
        Return a random string of given length
        :param length:
        :return: the generated string
        """
        chrlist = [chr(ord('A') + int(math.floor(random.random() * 26))) for i in range(length)]
        return "".join(chrlist)

    def _get_random_wrong_string(self, string_length):
        """
        Try 3 times to generate a random string not accepted by the function is_string_correct
        :return: None if failed to generate; otherwise the generated string
        """
        for i in range(3):
            str = self._get_random_string(string_length)
            if not self.is_string_correct(str):
                return str
        return None  # raise AssertionError("could not generate a random string that is not accepted by the automaton")

    def _get_almost_correct_string(self, length):
        """
        returns a string not accepted by function is_string_correct, which is however only slightly wrong
        kinds of almost correct strings (from mini-tasks):
        1 + 2: or case: choose all final states and don't allow entry into those states
        3: and case: choose one final state and don't allow entry into that state
        4: not case: either take the strategy from above or insert a bad not string (50/50)
        :return:
        """

        if len(self.negative_table) == 0 and len(self.positive_automaton.Final) == 0:
            return ""  # can happen if there's just "anything" as the language description

        avoid_states = set()
        insert_not_string = None

        if self.logical_op == self._or_string:
            avoid_states = self.positive_automaton.Final
        elif len(self.negative_table) == 0:
            avoid_states = random.sample(self.positive_automaton.Final, 1)
        else:
            if random.random() > 0.5 and len(self.positive_automaton.Final) > 0:
                avoid_states = random.sample(self.positive_automaton.Final, 1)
            else:
                insert_not_string = random.choice(self.negative_table)

        return self._get_string(length, False, avoid_states, insert_not_string)

    def get_wrong_string(self, length, randomization=1.0):
        """
        returns a string not accepted by function is_string_correct
        :param randomization:
        :return:
        """
        string = None
        if(randomization == 1.0):
            string = self._get_random_wrong_string(length)
        if(string == None):
            string = self._get_almost_correct_string(length)
        return string

    def _eval_positive(self, string):
        """
        Verify if the positive NFA recognises given word.
        :param str string: word to be recognised
        :rtype: bool
        """

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

        if last_confirmed + 1 != len(string) and not self.anything_allowed:
            # there is an unmatched character at position last_confirmed + 1
            return False

        if require_all and len(missing_final_states) != 0:
            return False

        return True

    def _eval_negative(self, string):
        """
        Verify if the negative NFA matches any ngram in the given word.
        :param str string: string to be recognised
        :rtype: bool
        """

        automaton = self.negative_automaton
        ilist = automaton.epsilonClosure(automaton.Initial)
        initial = ilist.copy()

        for i in range(len(string)):
            ilist = automaton.evalSymbol(ilist, string[i]).union(initial)  # loop here to be a matcher automaton
            if self._is_in_final_state(automaton, ilist):
                return True  # a single match is enough
        return False

    def is_string_correct(self, string):
        """
        make sure the string satisfies the positive and negative conditions
        :param string:
        :return:
        """
        pos = self._eval_positive(string)
        if not pos:
            return False

        neg = self._eval_negative(string)
        if neg:
            return False

        return True


def build_automaton(description, logical_op):
    """
    builds an automaton that is used for generating and recognizing the given language
    :param description:
    :param logical_op:
    :return:
    """
    return MiniTasksAutomatonInterface(description, logical_op)
