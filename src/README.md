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

### Constants used in Challenge Micro tasks

Name|Location|Description|Default value
---|---|---|---
REQUIRED_CONSECUTIVE_REWARDS|`MicroBase`|To pass the task instance, agent has to provide at least this number of correct answers in a row|10
success_tolerance|`MicroBase`|Once the task is sure that agent should already know everything it needs to solve the task perfectly, he will provide him some number of steps to prove it. The number is counted as `REQUIRED_CONSECUTIVE_REWARDS * (1 + success_tolerance)`|4
failed_task_tolerance|`MicroBase`|Once the period for proving the success is over, agent cannot successfully complete the instance, however it can still obtain new instructions (and possibly feedbacks). Amount of these new questions is counted as `number_of_already_asked_questions * (1 + failed_task_tolerance)`|1
ALPHABET_SIZE|`MicroTask1`-`MicroTask4`|Some tasks use just a subset of ASCII alphabet. This constant says how big the subset will be|4
MAPPING_SIZE|`Micro5Sub8`,`Micro5Sub9`,`Micro5Sub13`,`Micro5Sub16`-`Micro5Sub18`,`Micro17Task`|Some tasks can potentially generate a huge amount of question-answer pairs. This constant limit that number.|10; 8 at `Micro17Task`
