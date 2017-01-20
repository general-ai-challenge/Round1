
class DummyAutomatonInterface():

    def get_correct_string(self):
        return ''

    def get_wrong_string(self, randomization=1.0):
        return ''

    def is_string_correct(self, string):
        return False


def build_automaton(description, type):
    return DummyAutomatonInterface()
