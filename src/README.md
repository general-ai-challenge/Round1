## To run tests

`pip install -r requirements\dev.txt`
and then
`tox`

Coverage report is in `htmlcov` folder

If you want to see coverage report in the terminal as well, then run
`tox -- --cov-report term`

## To run app

Python 2
`pip install -r requirements\py2.txt`

Python 3
`pip install -r requirements\py3.txt`

## If you are on Windows
Download correct version of `curses` at http://www.lfd.uci.edu/~gohlke/pythonlibs/#curses

and install it with

`pip install curses-2.2-cp*.whl`