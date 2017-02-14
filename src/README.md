## To run tests

`pip install -r requirements\dev.txt`
and then
`tox`

Coverage report is in `htmlcov` folder

If you want to see coverage report in the terminal as well, then run
`tox -- --cov-report term`
Anything after that double-dash will be passed to underlying test runner (`nosetests`) as args

If you want to run tests in specific environment:
`tox -e py36-win`

If you want to run only specific set of tests:
`tox -- tasks.good_ai.tests.test_micro_tasks`

If you want to disable CommAI logging output in failed tests:
`tox -- --nologcapture`

## To run app

Python 2
`pip install -r requirements\py2.txt`

Python 3
`pip install -r requirements\py3.txt`

## If you are on Windows
Download correct version of `curses` at http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses

and install it with

`pip install curses-2.2-cp*.whl`

## Constants used in GoodAI Micro tasks

Name|Location|Description|Default value
---|---|---|---
REQUIRED_CONSECUTIVE_REWARDS|`MicroBase`|To pass the task instance, agent has to provide at least this number of correct answers in a row|10
success_tolerance|`MicroBase`|Once the task is sure that agent should already know everything it needs to solve the task perfectly, he will provide him some number of steps to prove it. The number is counted as `REQUIRED_CONSECUTIVE_REWARDS * (1 + success_tolerance)`|4
failed_task_tolerance|`MicroBase`|Once the period for proving the success is over, agent cannot successfully complete the instance, however it can still obtain new instructions (and possibly feedbacks). Amount of these new questions is counted as `number_of_already_asked_questions * (1 + failed_task_tolerance)`|1
ALPHABET_SIZE|`MicroTask1`-`MicroTask4`|Some tasks use just a subset of ASCII alphabet. This constant says how big the subset will be|4
MAPPING_SIZE|`Micro5Sub8`,`Micro5Sub9`,`Micro5Sub13`,`Micro5Sub16`-`Micro5Sub18`,`Micro17Task`|Some tasks can potentially generate a huge amount of question-answer pairs. This constant limit that number.|10; 8 at `Micro17Task`
