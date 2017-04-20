# General AI Challenge - Round 1 #

## Overview ##

This repository contains an environment and a set of tasks for the first round of the General AI Challenge.

The environment is a fork of environment [CommAI-env](https://github.com/facebookresearch/CommAI-env) from Facebook. It was modified for the Challenge in the following major ways:

1. The environment is byte-based instead of bit-based: communication occurs in bytes and not bits.
2. Reward is given as either -1, 0 or 1, not just 0 or 1.
3. Tasks for Round 1 of the General AI Challenge were added.

The repository also contains implementations of the following sets of tasks:

1. CommAI mini-tasks, described in [CommAI: Evaluating the first steps towards a useful general AI](https://arxiv.org/abs/1701.08954).
2. Challenge micro-tasks, described in the [Challenge specification document](https://mirror.general-ai-challenge.org/challenge_first_round_specifications.pdf).

## To run the environment

**Linux, Windows, (Mac)**

First clone the repository:

    git clone https://github.com/general-ai-challenge/Round1.git

Go into the cloned folder

    cd Round1

Then install dependencies (you will need at least Python 2.7):

- Python 2.7:	`pip install -r src/requirements/py2.txt`

- Python 3.5+:	`pip install -r src/requirements/py3.txt`

Check that your installation is working fine by running a human-interactive mode of the tasks:

	python src/run.py src/tasks_config.challenge.json -l learners.human_learner.ImmediateHumanLearner

For additional information, you can also refer to the installation instructions of original CommAI-env at [https://github.com/facebookresearch/CommAI-env](https://github.com/facebookresearch/CommAI-env)

Note: the environment should run fine on **Mac**, but this was not tested.

## If you are on Windows
Download correct version of `curses` at [http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses](http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses)

and install it with

	pip install curses-2.2-cp*.whl
	
When your `curses` support is running fine, you can run the interactive version of the environment 
with parameter `--curses`, which will switch the GUI to a nicer rendering.

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

## A note on original CommAI-env tasks
The challenge code is built on top of CommAI-env code. The original code also includes a number of tasks (folders `competition`, `micro` and `sample`). 
These original tasks are **not related to the challenge in any way**. 
We did not delete this code from the repository simply because
we wanted to allow you to browse through the original tasks if you wished to.

The original tasks are bit-based and if you want to run them, you should start the environment with parameter `--bitmode`. 
Also note that the original tasks are intended for python 2.6+ only, so you might encounter errors if using python 3.
 
We will not provide support for the original tasks - if you encounter an issue, please report it to the [original repository](https://github.com/facebookresearch/CommAI-env) . 


## Selected details of the environment

### Minor modifications
The environment contains some minor modifications (besides the major modifications listed above) when compared with the original version from Facebook.
The most notable are:

1. There is a new human-interactive mode that does not require the use of curses library (very useful for debugging).
2. Information that a task has ended (`result`) is now separated from `reward`. Reward can be sent even during the execution of a task.
3. There is a new scheduler - `ConsecutiveTaskScheduler`, which waits for a series of successess on a task before it passes execution to another task.

### Micro tasks system

During the training/testing of you agent, a sequential list consisting of one or 
more micro tasks is created. This list is then iterated and each of the tasks is 
presented to the agent until the agent solves all of them - or fails. 
Follows a detailed description of how micro-tasks are executed:

1. `ConsecutiveTaskScheduler` takes the next task. If it is at the end of the task list, it shuts down the environment.
2. A micro-task (inheriting from `MicroBase`) is initialized.
3. A new instance of the micro-task is started. The task instance starts showing questions to the agent.
4. If the agent does not respond, the task instance waits until it times out. Go to 3.
5. In a loop, the task instance processes the agent's response:
    1. If it is correct, the agent receives reward and `consecutive_reward` counter is incremented.
    2. If it is wrong, agent receives punishment (depends on the task) and `consecutive_reward` is set to 0.
    3. If it is indeferent, nothing happens.
6.  A task instance can finish for 3 reasons (which cause the loop at 5. to break):
    1. Agent solves the task instance before a soft time limit (`consecutive_reward` is high enough) - this counts as a correct solution. The agent proved that it understands the task.
    2. Agent solves the task instance after the soft time limit - this does not count as a correct solution.
    3. Agent does not solve the task instance and reaches the hard time limit.
    The soft and hard time limits are set dynamically from the code. See the method `check_if_task_instance_finished` for details.
7. If the task instance is solved correctly, scheduler's success counter is incremented. If it is equal or higher than the `success_threshold` (see table below), the task ends (go to 1.)
8. Otherwise, a new task instance is started (go to 3.)


How a task instance is evaluated:
1. The agent has only one way of finishing the task instance _successfully_ - to have a certain number of correct answers in a row within the provided time limit.
2. Once the task is sure that the agent already knows everything it needs to solve the task perfectly, it will provide the agent a certain number of questions to prove it. See variable `max_questions_for_success`. 
The number of questions is counted as `REQUIRED_CONSECUTIVE_REWARDS * (1 + SUCCESS_TOLERANCE)` (see table below for a description of the constants). 
If the agent answers the questions correctly, it finishes the task instance successfully. 
3. If the agent does not solve the task instance during this period, it can not 
finish this task instance successfully anymore. But it is still given some extra time to try to learn and solve the task. 
It is counted as `number_of_already_asked_questions * (1 + FAILED_TASK_TOLERANCE)` 
4. Once even this extra time is over, the task instance ends with a failure and a new task instance is created.

### Constants used in Challenge Micro tasks

Name|Location|Description|Default value
---|---|---|---
success_threshold | JSON config file | Number of required successful solutions of task instance for agent to proceed onto the next task
REQUIRED_CONSECUTIVE  _REWARDS | `MicroBase` | To pass the task instance, agent has to provide at least this number of correct answers in a row | 10
SUCCESS_TOLERANCE | `MicroBase` | Affects the size of period in which agent can solve the task instance successfully | 4
FAILED_TASK_TOLERANCE | `MicroBase` | Affects the maximum number of questions for one task instance | 1
ALPHABET_SIZE | `MicroTask1` -  `MicroTask4` | Some tasks use just a subset of ASCII alphabet. This constant says how big the subset will be | 4
MAPPING_SIZE | `Micro5Sub8`,  `Micro5Sub9`,  `Micro5Sub13`,  `Micro5Sub16` -  `Micro5Sub18`,  `Micro17Task` | Some tasks can potentially generate a huge amount of question-answer pairs. This constant limit that number. | 10; 8 at `Micro17Task`
