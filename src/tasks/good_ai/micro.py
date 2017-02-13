import random
import re
import string

from core.task import on_message, on_start, on_timeout
from core.task import Task
from tasks.good_ai.task_generator import TaskGenerator

REQUIRED_CONSECUTIVE_REWARDS = 10   # more or less arbitrary constant; high enough to prevent random solutions


class MicroBase(Task):
    reg_answer_end = r'.'
    failed_task_tolerance = 1.0
    success_tolerance = 4.0
    tasker = None

    def __init__(self, world=None):
        super(MicroBase, self).__init__(world=world, max_time=10000)
        self.skip_task_separator = True

    @staticmethod
    def get_task_generator():
        pass

    def agent_solved_instance_under_time_limit(self):
        '''
        Checks whether the agent solved task instance successfully
        '''
        return self.under_time_limit_for_successfull_solution() and self.consecutive_reward >= REQUIRED_CONSECUTIVE_REWARDS

    def agent_should_know_answers(self):
        '''
        Checks whether the information provided to agent was sufficient for it to know the correct solution to task instance
        Tasks may override this method - this is equal to knowing all the correct answers from first step
        '''
        return True

    def under_time_limit_for_successfull_solution(self):
        '''
        Checks whether the task is still in stage, where agent can successfully solve the task.
        This method does not check whether agent actually solved the task! Only if the time for the solution ran up or not!
        '''
        if self.max_questions_for_success:
            return self.questions_asked <= self.max_questions_for_success
        else:
            return True

    def get_original_question(self, question):
        return self.tasker.get_original_question(question)

    @on_start()
    def new_task_instance(self, event):
        self.tasker = self.get_task_generator()
        self.questions_asked = 0
        self.consecutive_reward = 0
        self.max_questions_nr = None
        self.max_questions_for_success = None
        self.agent_answer = ''
        self.give_instructions()

    def preprocess_answer(self, message):
        self.agent_answer += message[-1]    # add the newest char

    def provide_reward(self, reward):
        if reward > 0:
            self.consecutive_reward += 1
        elif reward < 0:
            self.consecutive_reward = 0
        if reward != 0:
            self.set_immediate_reward(reward)

    def question_answered(self, is_correct):
        self.questions_asked += 1

    def check_if_task_instance_finished(self):
        if self.agent_solved_instance_under_time_limit():    # agent solved instance
            self.set_result(True, provide_result_as_reward=False)
            return True

        if not self.max_questions_for_success and self.agent_should_know_answers():  # agent did not solve it but should know answers from now on
            self.max_questions_for_success = self.questions_asked + REQUIRED_CONSECUTIVE_REWARDS * (1.0 + self.success_tolerance)

        if not self.max_questions_nr and not self.under_time_limit_for_successfull_solution():  # agent failed but give him some time to learn task
            self.max_questions_nr = self.questions_asked * (1.0 + self.failed_task_tolerance)

        if self.max_questions_nr and self.questions_asked > self.max_questions_nr:  # agent used up all the extra time
            self.set_result(False, provide_result_as_reward=False)
            self._raise_timeout()
            return True
        return False

    def provide_feedback(self, correct):
        feedback_text = self.tasker.get_feedback_text(correct, self.question)
        self.set_message(feedback_text)

    def give_instructions(self):
        self.question, self.check_answer = self.tasker.get_task_instance()
        self.set_message(self.question)
        # internal buffer reset
        self.agent_answer = ''

    @on_message(r'.')
    def check_response(self, event):
        if not self._env.is_silent():
            if not event.message[-1] == ' ':
                self.set_immediate_reward(-1)
            return

        self.preprocess_answer(event.message)

        if not self._answer_ended(self.agent_answer):
            return      # agent is still speaking - do not check it yet

        # in case the message is not complete self.agent_answer should not be stripped
        answer = self.agent_answer.strip()
        if answer == '':
            answer = ' '

        finished, correct, reward = self.tasker.check_answer(answer, self.question)
        self.provide_reward(reward)

        # if one task sub-instance solved
        if finished:
            self.question_answered(correct)
            self.provide_feedback(correct)
            if not self.check_if_task_instance_finished():
                # give next instruction
                self.give_instructions()

    @on_timeout()   # while we use checking if agent solved instance ASAP - can this actually happen?
    def end_task_instance(self, event):
        self.set_result(False, provide_result_as_reward=False)

    @staticmethod
    def is_prefix(answer, correct_answer):
        if len(answer) >= len(correct_answer):
            return False
        return correct_answer.startswith(answer)

    def _answer_ended(self, message):
        return not (re.search(self.reg_answer_end, message) is None)


class Micro1Task(MicroBase):
    ALPHABET_SIZE = 10

    def __init__(self):
        self.base_alphabet = string.ascii_letters + string.digits + ' ,.!;?-'
        self.alphabet = random.sample(self.base_alphabet, self.ALPHABET_SIZE)
        super(Micro1Task, self).__init__()

    @on_start()
    def micro1_on_start(self, event):
        self.remaining_options = len(self.base_alphabet)
        self.should_know = False

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro1Task, self).question_answered(is_correct)
        if is_correct or self.remaining_options == 0:
            self.should_know = True
        if not is_correct:
            self.remaining_options -= 1

    def get_task_generator(self):
        alphabet = self.alphabet
        correct_answer = random.choice(alphabet)

        def micro1_question(self):
            return random.choice(alphabet), correct_answer
        return TaskGenerator(micro1_question)


def random_string_from(length, subset):
    return "".join(random.choice(subset) for _ in range(length))


def random_strings_from(charset, nr_of_strings, string_len_options=None, append=''):
    string_len_options = string_len_options or [1]
    result = []
    for _ in range(nr_of_strings):
        answer_len = random.choice(string_len_options)
        answer = random_string_from(answer_len, charset)
        result.append(answer + append)
    return result


class MicroMappingTask(MicroBase):

    task_gen_kwargs = {}

    def agent_should_know_answers(self):
        if len(self.known_mapping) > 0:
            return self.should_know
        else:
            return True

    def _get_mapping_options(self, mapping):
        '''
        This method is optional but if implemented, it should return dictionary where keys are all possible questions for agent and value is number of possible
        answers on that question from which agent has to find the right one.
        If mapping does not want to implement "agent_should_know_answers" it can implement this method and MicroMapping will use its "agent_should_know_answers"
        mechanism.
        '''
        return {}

    def _get_mapping(self):
        pass

    def question_answered(self, is_correct):
        super(MicroMappingTask, self).question_answered(is_correct)
        if len(self.known_mapping) == 0:    # not all Mapping tasks use the all_mapping_options concept
            return
        if self.question[-1] == '.' and len(self.question) > 1:
            question = self.question[:-1]
        else:
            question = self.question
        if is_correct:
            self.known_mapping[question] = 1
        else:
            self.known_mapping[question] = max(self.known_mapping[question] - 1, 1)

        if all(x == 1 for x in self.known_mapping.values()):
            self.should_know = True

    def get_task_generator(self):
        mapping = self._get_mapping()
        self.known_mapping = self._get_mapping_options(mapping)
        self.should_know = False

        def multigen(d):
            while True:
                k = list(d.keys()) * len(d.keys())
                random.shuffle(k)
                for i in k:
                    yield i
        gen = multigen(mapping)

        def micro_mapping_question(self):
            def micro_mapping_reward(answer, question):
                key = self.get_original_question(question)
                if len(answer) > 0 and MicroBase.is_prefix(answer, mapping[key]):
                    return None, 0
                correct = answer == mapping[key]
                return correct, 1 if correct else -1
            return next(gen), micro_mapping_reward
        return TaskGenerator(micro_mapping_question, **self.task_gen_kwargs)

    # this could be solved by less code, but I chose the explicit way
    def _get_simple_feedback_provider(self, mapping):
        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            return mapping[key]
        return feedback_provider

    def _get_prepend_feedback_provider(self, mapping, prepend_set, prepend_len_options=None):
        prepend_len_options = prepend_len_options or [1]

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            prepend_len = random.choice(prepend_len_options)
            prepend = random_string_from(prepend_len, prepend_set)
            return prepend + mapping[key]
        return feedback_provider


class Micro2Task(MicroMappingTask):
    base_alphabet = string.ascii_lowercase
    alphabet = random.sample(base_alphabet, 4)

    def __init__(self):
        super(Micro2Task, self).__init__()

    @on_start()
    def micro2_on_start(self, event):
        self.remaining_options = len(self.base_alphabet)

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro2Task, self).question_answered(is_correct)
        if (is_correct and self.question in self.alphabet) or self.remaining_options == 0:
            self.should_know = True
        if not is_correct:
            self.remaining_options -= 1

    def _get_mapping(self):
        correct_answer = random.choice(self.alphabet)
        mapping = {x: correct_answer for x in self.alphabet}
        for c in ' !":?.,;':
            mapping[c] = c
        return mapping


class Micro3Task(MicroMappingTask):
    base_alphabet = string.ascii_lowercase
    alphabet = random.sample(base_alphabet, 4)

    def _get_mapping_options(self, mapping):
        result = {x: len(self.base_alphabet) for x in self.alphabet}
        for c in ' !":?.,;':
            result[c] = 1
        return result

    def _get_mapping(self):
        permutation = ''.join(random.sample(self.alphabet, len(self.alphabet)))
        mapping = dict(zip(self.alphabet, permutation))
        for c in ' !":?.,;':
            mapping[c] = c
        return mapping


class Micro4Task(MicroMappingTask):
    alphabet = random.sample(string.ascii_lowercase + ' !":?.,;', 4)

    def _get_mapping(self):
        alphabet = self.alphabet
        mapping = dict(zip(alphabet, alphabet))
        return mapping


class FeedbackMappingTaskMixin(MicroMappingTask):
    '''
    This mixin should be used when the task uses feedback and we assume the feedback can be exploited already.
    The only one occurrence is needed for every key from mapping.
    '''

    def _get_mapping_options(self, mapping):
        keys = mapping.keys()
        return {x: 2 for x in keys}


class Micro5Sub1Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {}

    def _get_mapping(self):
        numbers = '0123456789'
        permutation = ''.join(random.sample(numbers, len(numbers)))
        mapping = dict(zip(numbers, permutation))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub2Task(Micro5Sub1Task):
    task_gen_kwargs = {'feedback_sep': ';'}


class Micro5Sub3Task(Micro5Sub1Task):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}


class Micro5Sub4Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random_string_from(2, numbers) for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub5Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub6Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            if is_correct:
                return mapping[key][:-1]    # remove trailing dot
            return mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


class Micro5Sub7Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        answers = random_strings_from(numbers, len(numbers), [1, 2], '.')
        mapping = dict(zip(numbers, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub8Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        nr_questions = 10
        questions = random_strings_from(numbers, nr_questions, [2])
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub9Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        nr_questions = 10
        questions = random_strings_from(numbers, nr_questions, [1, 2])
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# TODO: should be the ignored part be always the same for the same inputs or can it change? - this version changes it
class Micro5Sub10Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_prepend_feedback_provider(mapping, numbers)
        return mapping


class Micro5Sub11Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        def feedback_provider(is_correct, question):
            key = self.get_original_question(question)
            do_prepend = random.choice([True, False])
            if do_prepend:
                prepend = random.choice(numbers)
            else:
                prepend = ''
            return prepend + mapping[key]
        self.task_gen_kwargs['provide_feedback'] = feedback_provider
        return mapping


# stems from 5.7
# TODO: description says "either 3 or 4 or 5 chars. Shown example for 3
# chars". So will it be always the same size of feedback for on task
# instance? Or can it be mixed? - this version is mixed
# same question for 5.13, 5.14, 5.15, 5.16, 5.17 and 5.18
class Micro5Sub12Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        answers = random_strings_from(numbers, len(numbers), [3, 4, 5], '.')
        mapping = dict(zip(numbers, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# stems from 5.9
class Micro5Sub13Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        nr_questions = 10
        questions = random_strings_from(numbers, nr_questions, [3, 4, 5])
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# stems from 5.12
class Micro5Sub14Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        mapping = {x: random.choice(numbers) + '.' for x in numbers}

        self.task_gen_kwargs['provide_feedback'] = self._get_prepend_feedback_provider(mapping, numbers, [2, 3, 4])
        return mapping


class Micro5Sub15Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        answers = random_strings_from(numbers, len(numbers), range(1, 6), '.')
        mapping = dict(zip(numbers, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub16Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        nr_questions = 10
        questions = random_strings_from(numbers, nr_questions, range(1, 6))
        mapping = {x: random.choice(numbers) + '.' for x in questions}

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


class Micro5Sub17Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        nr_questions = 10
        questions = random_strings_from(numbers, nr_questions, range(1, 6))
        answers = random_strings_from(numbers, len(questions), range(1, 6), '.')
        mapping = dict(zip(questions, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


# stems from 5.17
class Micro5Sub18Task(FeedbackMappingTaskMixin, MicroMappingTask):
    task_gen_kwargs = {'input_sep': '.', 'feedback_sep': ';'}

    def _get_mapping(self):
        numbers = '0123456789'
        nr_questions = 10
        questions = random_strings_from(numbers, nr_questions, range(1, 11))
        answers = random_strings_from(numbers, len(questions), range(1, 11), '.')
        mapping = dict(zip(questions, answers))

        self.task_gen_kwargs['provide_feedback'] = self._get_simple_feedback_provider(mapping)
        return mapping


def load_dictionary(file_name):
    with open(file_name) as f:
        content = f.readlines()
    return [x.strip() for x in content]


class Micro6Sub1Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro6_1_question(self):
            correct_answer = random.choice(string.ascii_lowercase) + '.'
            question = "say: {}".format(correct_answer)

            def micro6_1_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '! ' + correct_answer
            return question, [correct_answer], micro6_1_feedback
        return TaskGenerator(micro6_1_question, '', None, ';')


class Micro6Sub2Task(MicroBase):
    reg_answer_end = r'\.'
    FILE_NAME = 'res/dict_gsl.txt'

    def get_task_generator(self):
        valid_words = load_dictionary(self.FILE_NAME)

        def micro6_2_question(self):
            word = random.choice(valid_words) + '.'
            question = "say: {}".format(word)

            def micro6_2_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '! ' + word
            return question, [word], micro6_2_feedback
        return TaskGenerator(micro6_2_question, '', None, ';')


class Micro6Sub3Task(MicroBase):
    reg_answer_end = r'\.'
    FILE_NAME = 'res/dict_gsl.txt'

    def get_task_generator(self):
        valid_words = load_dictionary(self.FILE_NAME)

        def micro6_3_question(self):
            sentence = random.choice(valid_words) + ' ' + random.choice(valid_words) + '.'
            question = "say: {}".format(sentence)

            def micro6_3_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '! ' + sentence
            return question, [sentence], micro6_3_feedback
        return TaskGenerator(micro6_3_question, '', None, ';')


class Micro7Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro7_question(self):
            alphabet = string.ascii_lowercase
            sentence = "{}{}{}{}{}.".format(' ' * random.randint(0, 6), random.choice(alphabet), ' ' * random.randint(0, 6),
                                            random.choice(alphabet), ' ' * random.randint(0, 6))
            question = "say: {}".format(sentence)
            sentence = re.sub(' +', ' ', sentence).strip()

            def micro7_feedback(is_correct, question):
                reaction = "correct" if is_correct else "false"
                return reaction + '!' + sentence
                print("sentence: ".format(sentence))
            return question, [sentence], micro7_feedback

        return TaskGenerator(micro7_question, '', None, ';')


class Micro8Sub1Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro8_question(self):
            valid_words = string.ascii_lowercase
            word = random.choice(valid_words) + '.'
            question = "spell: {}".format(word)
            sentence = " ".join(word)

            def micro8_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                return reaction + '! ' + sentence
            return question, [sentence], micro8_feedback
        return TaskGenerator(micro8_question, '', None, ';')


class Micro8Sub2Task(MicroBase):
    reg_answer_end = r'\.'
    FILE_NAME = 'res/dict_gsl.txt'

    def get_task_generator(self):
        def micro8_question(self):
            valid_words = load_dictionary('res/dict_gsl.txt')
            word = random.choice(valid_words) + '.'
            question = "spell: {}".format(word)
            sentence = " ".join(word)

            def micro8_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                return reaction + '! ' + sentence

            return question, [sentence], micro8_feedback

        return TaskGenerator(micro8_question, '', None, ';')


class Micro8Sub3Task(MicroBase):
    reg_answer_end = r'\.'
    FILE_NAME = 'res/dict_gsl.txt'

    def get_task_generator(self):
        def micro8_question(self):
            valid_words = load_dictionary('res/dict_gsl.txt')
            word = random.choice(valid_words)
            joint = random.choice(['-', '#', ','])
            question = "interleave: " + word + ' by ' + joint + '.'
            sentence = joint.join(word) + '.'

            def micro8_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                return reaction + '! ' + sentence

            return question, [sentence], micro8_feedback

        return TaskGenerator(micro8_question, '', None, ';')


class Micro9Task(MicroBase):
    reg_answer_end = r'\.'
    FILE_NAME = 'res/dict_gsl.txt'

    def get_task_generator(self):
        def micro9_question(self):
            valid_words = load_dictionary('res/dict_gsl.txt')
            n = random.randint(2, 3)
            questions = []
            words = []
            for i in range(0, n):
                word = random.choice(valid_words)
                words.append(word)
                questions.append('say: {}'.format(word))
            question = ' '.join(questions) + '.'
            sentence = ' '.join(words) + '.'

            def micro9_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro9_feedback
        return TaskGenerator(micro9_question, '', None, ';')


class Micro10Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro10_question(self):
            actions = ['reverse', 'concatenate', 'interleave']
            action = random.choice(actions)
            valid_words = ["ab", "ac", "ad", "bc", "bd", "cd"]
            questions = []
            words = []
            for i in range(0, 2):
                word = random.choice(valid_words)
                words.append(word)
                questions.append('say: {}'.format(word))
            question = ' '.join(questions) + ' ' + action + ':.'
            if action == 'reverse':
                words.reverse()
                sentence = ' '.join(words)
            elif action == 'concatenate':
                sentence = ''.join(words)
            else:
                sentence = [val for pair in zip(words[0], words[1]) for val in pair]
                sentence = ''.join(sentence)
            sentence += '.'

            def micro10_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro10_feedback
        return TaskGenerator(micro10_question, '', None, ';')


class Micro11Task(MicroBase):
    reg_answer_end = r'\.'

    @staticmethod
    def string_special_union(str1, str2):
        if str1.find(str2) >= 0:
            return str1
        return str1 + str2

    @staticmethod
    def string_special_exclude(str1, str2):
        return str1.replace(str2, '')

    def get_task_generator(self):
        def micro11_question(self):
            actions = ['union', 'exclude']
            action = random.choice(actions)
            valid_words = ["abc", "acd", "adc", "bcd", "bda", "cdb"]
            valid_second_words = ["a", "b", "c", "d"]
            word = random.choice(valid_words)
            second_word = random.choice(valid_second_words)
            question = 'say: {} say: {} {}:.'.format(word, second_word, action)
            if action == 'union':
                sentence = Micro11Task.string_special_union(word, second_word)
            else:
                sentence = Micro11Task.string_special_exclude(word, second_word)
            sentence += '.'

            def micro11_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro11_feedback
        return TaskGenerator(micro11_question, '', None, ';')


class Micro12Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro12_question(self):
            alphabet = string.ascii_lowercase
            idx = random.randint(0, len(alphabet) - 2)
            question = 'after {} comes what:.'.format(alphabet[idx])
            sentence = alphabet[idx + 1]
            sentence += '.'

            def micro12_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            return question, [sentence], micro12_feedback
        return TaskGenerator(micro12_question, '', None, ';')


class Micro13Task(MicroBase):
    reg_answer_end = r'\.'
    m8 = Micro8Sub2Task()
    m9 = Micro9Task()
    m10 = Micro10Task()
    m11 = Micro11Task()

    def get_task_generator(self):
        tasks = [self.m8, self.m9, self.m10, self.m11]
        task = random.choice(tasks)
        return task.get_task_generator()


class Micro15Sub1Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro15_question(self):
            def micro15_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            action = random.randint(1, 4)
            words = list('abcde')
            # and
            if action == 1:
                word1 = random.choice(words)
                word2 = random.choice(words)
                question = ' say: {} and {}.'.format(word1, word2)
                sentence1 = '{}{}.'.format(word1, word2)
                sentence2 = '{}{}.'.format(word2, word1)
                sentence = random.choice([sentence1, sentence2])
                return question, [sentence1, sentence2], micro15_feedback
            # or
            elif action == 2:
                word1 = random.choice(words)
                word2 = random.choice(words)
                question = ' say: {} or {}.'.format(word1, word2)
                sentence = '{}.'.format(random.choice([word1, word2]))

                def or_reward(answer, question=''):
                    correct = answer.find(word1) >= 0 or answer.find(word2) >= 0
                    return correct, 1 if correct else -1
                return question, or_reward, micro15_feedback
            # anything and not
            elif action == 3:
                word1 = 'anything'
                word2 = random.choice(words)
                words.remove(word2)
                question = ' say: {} and not {}.'.format(word1, word2)
                sentence = random.choice(words)

                def anything_and_not_reward(answer, question=''):
                    correct = answer.find(word2) < 0
                    return correct, 1 if correct else -1
                return question, anything_and_not_reward, micro15_feedback
            # or but not
            else:
                word1 = random.choice(words)
                words.remove(word1)
                word2 = random.choice(words)
                words.remove(word2)
                word3 = random.choice([word1, word2, random.choice(words)])
                question = ' say: {} or {} but not {}.'.format(word1, word2, word3)
                correct_word = [word1, word2]
                if word3 in correct_word:
                    correct_word.remove(word3)
                sentence = random.choice(correct_word)

                def or_but_not_reward(answer, question=''):
                    correct = answer.find(word3) < 0 and (answer.find(word2) >= 0 or answer.find(word1) >= 0)
                    return correct, 1 if correct else -1
                return question, or_but_not_reward, micro15_feedback
        return TaskGenerator(micro15_question, '', None, ';')


class Micro15Sub2Task(MicroBase):
    reg_answer_end = r'\.'

    def get_task_generator(self):
        def micro15sub2_question(self):
            def micro15sub2_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            alphabet = string.ascii_lowercase
            actions = ['or', 'and']
            action = random.choice(actions)
            operands = random.randint(2, 4)
            words = []
            for i in range(operands):
                word_length = random.randint(1, 3)
                words.append(''.join(random.sample(alphabet, word_length)))
            clause = (' ' + action + ' ').join(words)
            if action == 'or':
                sentence = random.choice([item for item in words])

                def or_but_not_reward(answer, question=''):
                    correct = any(answer.find(word) >= 0 for word in words)
                    return correct, 1 if correct else -1
                question = 'say: ' + clause + '.'
                return question, or_but_not_reward, micro15sub2_feedback
            else:
                sentence = ''.join(words)
                sentence += '.'
                question = 'say: ' + clause + '.'
                return question, [sentence], micro15sub2_feedback

        return TaskGenerator(micro15sub2_question, '', None, ';')


class Micro17Task(MicroBase):
    reg_answer_end = r'\.'
    MAPPING_SIZE = 8
    FILE_NAME = 'res/dict_gsl.txt'
    failed_task_tolerance = 2.0

    @on_start()
    def new_task_instance(self, event):
        super(Micro17Task, self).new_task_instance(event)
        self.should_know = False
        self.actual_key = ''

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro17Task, self).question_answered(is_correct)
        key = self.question.split()[-1].split('.')[0]
        self.mapping_check[key] = True
        if all(self.mapping_check.values()):
            self.should_know = True

    def get_task_generator(self):
        content = load_dictionary(self.FILE_NAME)
        vocabulary = content[:200]
        mapping = dict(zip(random.sample(vocabulary, self.MAPPING_SIZE),
                           random.sample(vocabulary, self.MAPPING_SIZE)))
        keys = list(mapping.keys())
        self.mapping_check = {key: False for key in keys}

        def micro17_question(self):
            def micro17_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            self.key_idx = random.randint(0, len(keys) - 1)
            word1 = keys[self.key_idx]
            word2 = mapping[word1]
            question = 'random_map: ' + word1 + '.'
            sentence = word2 + '.'
            return question, [sentence], micro17_feedback

        return TaskGenerator(micro17_question, '', None, ';')


class Micro18Task(MicroBase):
    reg_answer_end = r'\.'
    failed_task_tolerance = 2.0

    @on_start()
    def new_task_instance(self, event):
        super(Micro18Task, self).new_task_instance(event)
        self.should_know = False

    def agent_should_know_answers(self):
        return self.should_know

    def question_answered(self, is_correct):
        super(Micro18Task, self).question_answered(is_correct)
        key = self.question.split()[-1].split('.')[0]
        self.mapping_check[key] = True
        if all(self.mapping_check.values()):
            self.should_know = True

    def get_task_generator(self):
        sequence1 = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
        sequence2 = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth']
        sequence3 = ['ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
        sequence4 = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
                     'sixteen', 'seventeen', 'eighteen', 'nineteen']

        chosen_sequence = random.choice([sequence1, sequence2, sequence3, sequence4])
        if random.randint(0, 2) > 0:
            chosen_sequence.reverse()

        self.mapping_check = {key: False for key in chosen_sequence[0:-1]}

        def micro18_question(self):
            def micro18_feedback(is_correct, question):
                reaction = "good job" if is_correct else "wrong"
                if not is_correct:
                    return reaction + '! ' + sentence
                else:
                    return reaction + '! '
            idx = random.randint(0, len(chosen_sequence) - 2)
            word = chosen_sequence[idx]
            question = 'say next after: ' + word + '.'
            sentence = chosen_sequence[idx + 1] + '.'
            return question, [sentence], micro18_feedback

        return TaskGenerator(micro18_question, '', None, ';')


class Micro19Task(MicroBase):
    reg_answer_end = r'\.'
    m9 = Micro9Task()
    m10 = Micro10Task()
    m11 = Micro11Task()
    m12 = Micro12Task()
    failed_task_tolerance = 2.0
    synonyms = {'say:': ['say:', 'print:', 'write:'],
                'and': ['and', 'together with', '&', 'also'],
                'or': ['or', 'alternative', '/'],
                'after': ['after', 'behind', 'next'],
                'union': ['union', 'consolidate', 'joint'],
                'exclude': ['exclude', 'prohibit', 'ignore', 'remove']}
    synonym_list = ["say:", 'and', 'after', 'union', 'exclude']

    @on_start()
    def new_task_instance(self, event):
        super(Micro19Task, self).new_task_instance(event)
        self.tasks = []
        self.should_know = False

    def get_task_generator(self):
        # choose task randomly, but provide all n tasks in n tries
        if len(self.tasks) == 0:
            self.tasks = [self.m9, self.m10, self.m11, self.m12]
        task = random.choice(self.tasks)
        self.tasks.remove(task)
        task_generator = task.get_task_generator()
        func_inner = task_generator.instancer

        synonym_list = self.synonym_list
        get_random_synonym = self.get_random_synonym

        def func_outer(self):
            question, a, b = func_inner(self)
            for synonym in synonym_list:
                question = question.replace(synonym, get_random_synonym(synonym))
            return question, a, b
        task_generator.instancer = func_outer
        return task_generator

    def get_random_synonym(self, word):
        return random.choice(self.synonyms[word])


class Micro20Task(Micro19Task):
    FILE_NAME = 'res/dict_gsl.txt'

    @on_start()
    def new_task_instance(self, event):
        super(Micro20Task, self).new_task_instance(event)
        self.tasks = []

    def get_task_generator(self):
        content = load_dictionary(self.FILE_NAME)
        vocabulary = content[200:400]
        self.synonyms = {o: s for (o, s) in zip(self.synonym_list, random.sample(vocabulary, len(self.synonym_list)))}

        # choose task randomly, but provide all n tasks in n tries
        if len(self.tasks) == 0:
            self.tasks = [self.m9, self.m10, self.m11, self.m12]
        task = random.choice(self.tasks)
        self.tasks.remove(task)

        task_generator = task.get_task_generator()
        func_inner = task_generator.instancer

        synonym_list = self.synonym_list
        get_synonym = self.get_synonym

        def func_outer(self):
            question, a, b = func_inner(self)
            synonym_present = [synonym for synonym in synonym_list if question.find(synonym) >= 0]
            synonym = random.choice(synonym_present)
            new_synonym = get_synonym(synonym)
            question = question.replace(synonym, new_synonym)
            question = new_synonym + " is as " + synonym + ' - ' + question
            return question, a, b
        task_generator.instancer = func_outer
        return task_generator

    def get_synonym(self, word):
        return self.synonyms[word]
