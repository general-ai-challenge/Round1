# General AI Challenge - Round 1 #

## Overview ##

This repository contains an environment and a set of tasks for the first round of the General AI Challenge.

The environment is a fork of environment [CommAI-env](https://github.com/facebookresearch/CommAI-env) from Facebook. It was modified for the Challenge in the following major ways:

1. The environment is byte-based instead of bit-based: communication occurs in bytes and not bits.
2. Reward is given as either -1, 0 or 1, not just 0 or 1.
3. Tasks for Round 1 of the General AI Challenge were added.

The repository contains implementations of CommAI mini-tasks, which are described in [CommAI: Evaluating the first steps towards a useful general AI](https://arxiv.org/abs/1701.08954), and implementations of micro-tasks described in [link to specification].

## To run the environment

**Linux, Windows, (Mac)**

First clone the repository:

	git clone https://github.com/general-ai-challenge/Round1.git

Then install dependencies (you will need at least Python 2.7):

- Python 2.7:	`pip install -r requirements\py2.txt`

- Python 3.5+:	`pip install -r requirements\py3.txt`

Check that your installation is working fine by running a human-interactive mode of the tasks:

	python src\run.py tasks_config.micro.json -l learners.human_learner.ImmediateHumanLearner

For additional information, you can also refer to the installation instructions of original CommAI-env at [https://github.com/facebookresearch/CommAI-env](https://github.com/facebookresearch/CommAI-env)

Note: the environment should run fine on **Mac**, but this was not tested.

## If you are on Windows
Download correct version of `curses` at [http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses](http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses)

and install it with

	pip install curses-2.2-cp*.whl

## To run unit tests

	pip install -r requirements\dev.txt

and then

	tox

Coverage report is in `htmlcov` folder

If you want to see coverage report in the terminal as well, run

	tox -- --cov-report term

Anything after that double-dash will be passed to the underlying test runner (`nosetests`) as args

If you want to run tests in specific environment (for instance, python 3.6 on Windows):

	tox -e py36-win

If you want to run only a specific set of tests:

	tox -- tasks.challenge.round1.tests.test_micro_tasks

If you want to disable logging of output in failed tests:

	tox -- --nologcapture

Note that you can also use other unit test frameworks.

## To implement your solution
You should implement your own `learner` which will solve the micro-tasks and the mini-tasks in a gradual way. Example learners are available in the `learners` directory. The most basic learner shown there is the `SampleRepeatingLearner`, which just sends back to the environment whatever it receives from it.

You might need to design your own task(s). To do that, refer to the challenge tasks in the folder `tasks/challenge/round1` for inspiration. Simpler tasks, like `Micro1Task`, are a good place to start.

## Selected details of the environment

### Minor modifications
The environment contains some minor modifications (besides the major modifications listed above) when compared with the original version from Facebook.
The most notable are:

1. There is a new human-interactive mode that does not require the use of curses library (very useful for debugging).
2. Information that a task has ended (`result`) is now separated from `reward`. Reward can be sent even during the execution of a task.
3. There is a new scheduler - `ConsecutiveTaskScheduler`, which waits for a series of successess on a task before it passes execution to another task.

## Micro tasks system

During the test of you agent, a sequential list consisting of one or more micro tasks is created. This list is then iterated and each of the tasks is presented to the agent until the agent solves all of them - or fails. The process is following

1. `ConsecutiveTaskScheduler` takes next task. If it is at the end of the task list, it goes back to first one.
2. Micro task (inheriting from `MicroBase`) is initialized.
3. New task instance is started
4. Task instance presents agent next question.
5. If the agent does not respond, task waits until it times out.
6. Task processes the agent's response.
    1. If it is correct, agent receives reward and `consecutive_reward` counter is incremented
    2. If it is wrong, agent receives punishment (depends on the task) and `consecutive_reward` is set to 0
7.  If the task instance is not finished yet, new question is presented to agent (go to 4.)
8.  Task instance can end for 2 reasons
    1. Agent proved that he understands the task
    2. Agent did not finished the task in the limit - there are two of them
        1. Limit 1 - maximum number of questions being asked (see FAILED_TASK_TOLERANCE)
        2. Limit 2 - maximum number of steps to run the task
9. If the task instance is solved correctly, scheduler's success counter is incremented. If it is equal or higher than the `success_threshold` (see table below), the task ends (go to 1.)
10. Otherwise, new task instance start (go to 3.)

How the task instance is evaluated
1. Agent has only one way of solving the task instance - to have a certain number of correct answers in a row (see table below for details)
2. Once the task is sure that the agent already knows everything it needs to solve the task perfectly, it will provide the agent certain number of questions to prove it (`max_questions_for_success` variable). The number of questions is counted as `REQUIRED_CONSECUTIVE_REWARDS * (1 + SUCCESS_TOLERANCE)` (see table below for description of constants).
3. If the agent does not solve the task instance during this period, it failed. But it is still given some extra time to learn the task. It is counted as `number_of_already_asked_questions * (1 + FAILED_TASK_TOLERANCE)` (see table below for description of constants).
4. Once even this period is over, the task instance ends.

### Constants used in Challenge Micro tasks

Name|Location|Description|Default value
---|---|---|---
success_threshold | JSON config file | Number of required successful solutions of task instance for agent to proceed onto the next task
REQUIRED_CONSECUTIVE_REWARDS | `MicroBase` | To pass the task instance, agent has to provide at least this number of correct answers in a row | 10
SUCCESS_TOLERANCE | `MicroBase` | Affects the size of period in which agent can solve the task instance successfully | 4
FAILED_TASK_TOLERANCE | `MicroBase` | Affects the maximum number of questions for one task instance | 1
ALPHABET_SIZE | `MicroTask1`-`MicroTask4` | Some tasks use just a subset of ASCII alphabet. This constant says how big the subset will be | 4
MAPPING_SIZE | `Micro5Sub8`,`Micro5Sub9`,`Micro5Sub13`,`Micro5Sub16`-`Micro5Sub18`,`Micro17Task` | Some tasks can potentially generate a huge amount of question-answer pairs. This constant limit that number. | 10; 8 at `Micro17Task`
