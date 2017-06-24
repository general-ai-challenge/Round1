# -*- coding: utf-8
# 'version': '0.2'
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

import os
import logging
import logging.config
import operator
from optparse import OptionParser
from core.serializer import StandardSerializer
from core.environment import Environment
from core.config_loader import JSONConfigLoader, PythonConfigLoader
import learners
from core.session import Session


def main():
    """ retrieve the task configuration file.  we choose how the environment will produce and interpret the bit signal. 
     create a learner (the human learner takes the serializer).  create our tasks and put them into a scheduler to 
     serve them.  construct an environment.  a learning session.  setup view.  send the interface to the human learner. 
      this was  not a human learner, nothing to do. ok guys, talk

    
    :return: 
    """
    setup_logging()
    op = OptionParser("Usage: %prog [options] " "(tasks_config.json | tasks_config.py)")
    op.add_option('-o', '--output', default='results.out', help='File where the simulation results are saved.')
    op.add_option(
        '--scramble', action='store_true', default=False, help='Randomly scramble the words in the tasks for ' 
                                                               'a human player.')
    op.add_option('-w', '--show-world', action='store_true', default=False,
                  help='shows a visualization of the world in the console ' '(mainly for debugging)')
    op.add_option('-d', '--time-delay', default=0, type=float, help='adds some delay between each timestep for easier'
                  ' visualization.')
    op.add_option('-l', '--learner', default='learners.human_learner.HumanLearner', help='Defines the type of learner.')
    op.add_option('-v', '--view', default='BaseView', help='Viewing mode.')
    op.add_option('--learner-cmd', help='The cmd to run to launch RemoteLearner.')
    op.add_option('--learner-port', default=5556, help='Port on which to accept remote learner.')
    op.add_option(
        '--max-reward-per-task', default=2147483647, type=int, help='Maximum reward that we can give to a learner for' 
                                                                    ' a given task.')
    op.add_option(
        '--curses', action='store_true', default=False, help='Uses standard output instead of curses library.')
    op.add_option('--bit-mode', action='store_true', default=False, help='Environment receives input in bytes.')
    opt, args = op.parse_args()
    if len(args) == 0:
        op.error("Tasks schedule configuration file required.")
    tasks_config_file = args[0]
    logger = logging.getLogger(__name__)
    logger.info("Starting new evaluation session")
    serializer = StandardSerializer()
    learner = create_learner(opt.learner, serializer, opt.learner_cmd, opt.learner_port, not opt.bit_mode)
    task_scheduler = create_tasks_from_config(tasks_config_file)
    env = Environment(serializer, task_scheduler, opt.scramble, opt.max_reward_per_task, not opt.bit_mode)
    session = Session(env, learner, opt.time_delay)
    view = create_view(opt.view, opt.learner, env, session, serializer, opt.show_world, opt.curses, not opt.bit_mode)
    try:
        learner.set_view(view)
    except AttributeError:
        pass
    try:
        view.initialize()
        session.run()
    except BaseException:
        view.finalize()
        save_results(session, opt.output)
        raise
    else:
        view.finalize()


def create_view(view_type, learner_type, env, session, serializer, show_world, use_curses, byte_mode):
    """
    
    :param view_type: 
    :param learner_type: 
    :param env: 
    :param session: 
    :param serializer: 
    :param show_world: 
    :param use_curses: 
    :param byte_mode: 
    :return: 
    """
    if not use_curses:
        from view.win_console import StdInOutView, StdOutView
        # TODO unreselved ref win_conole, StdInOutView, StdOutView not found
        if learner_type.split('.')[0:2] == ['learners', 'human_learner'] or view_type == 'ConsoleView':
            return StdInOutView(env, session, serializer, show_world, byte_mode)
        else:
            return StdOutView(env, session)
    else:
        from view.console import ConsoleView, BaseView
        # TODO unresolved ref console, ConsoleView, BaseView not found
        if learner_type.split('.')[0:2] == ['learners', 'human_learner'] or view_type == 'ConsoleView':
            return ConsoleView(env, session, serializer, show_world, byte_mode)
        else:
            return BaseView(env, session)


def create_learner(learner_type, serializer, learner_cmd, learner_port=None, byte_mode=False):
    """ dynamically load the class given by learner_type.  separate the module from the class name.  import the 
    module (and the class within it) instantiate the learner
    
    :param learner_type: 
    :param serializer: 
    :param learner_cmd: 
    :param learner_port: 
    :param byte_mode: 
    :return: 
    """
    if learner_type.split('.')[0:2] == ['learners', 'human_learner']:
        c = learner_type.split('.')[2]
        if c == 'HumanLearner':
            return learners.human_learner.HumanLearner(serializer, byte_mode)
        elif c == 'ImmediateHumanLearner':
            return learners.human_learner.ImmediateHumanLearner(serializer, byte_mode)
        elif c == 'HaltOnDotHumanLearner':
            return learners.human_learner.HaltOnDotHumanLearner(serializer, byte_mode)
    else:
        path = learner_type.split('.')
        mod, cname = '.'.join(path[:-1]), path[-1]
        m = __import__(mod, fromlist=[cname])
        c = getattr(m, cname)
        return c(learner_cmd, learner_port) if 'RemoteLearner' in cname else c()


def create_tasks_from_config(tasks_config_file):
    """ Returns a TaskScheduler based on either:
    - a json configuration file.
    - a python module with a function create_tasks that does the job of returning the task scheduler.
    
    :param tasks_config_file: 
    :return: 
    """
    fformat = tasks_config_file.split('.')[-1]
    if fformat == 'json':
        config_loader = JSONConfigLoader()
    elif fformat == 'py':
        config_loader = PythonConfigLoader()
    else:
        raise RuntimeError("Unknown configuration file format '.{fformat}' of"
                           " {filename}".format(fformat=fformat, filename=tasks_config_file))
    return config_loader.create_tasks(tasks_config_file)


def save_results(session, output_file):
    """ nothing to save
    
    :param session: 
    :param output_file: 
    :return: 
    """
    if session.get_total_time() == 0:
        return
    with open(output_file, 'w') as fout:
        print('* General results', file=fout)
        print('Average reward: {avg_reward}'.format(
            avg_reward=session.get_total_reward() / session.get_total_time()), file=fout)
        print('Total time: {time}'.format(time=session.get_total_time()), file=fout)
        print('Total reward: {reward}'.format(reward=session.get_total_reward()), file=fout)
        print('* Average reward per task', file=fout)
        for task, t in sorted(session.get_task_time().items(), key=operator.itemgetter(1)):
            r = session.get_reward_per_task()[task]
            print('{task_name}: {avg_reward}'.format(task_name=task, avg_reward=r / t), file=fout)
        print('* Total reward per task', file=fout)
        for task, r in sorted(session.get_reward_per_task().items(), key=operator.itemgetter(1), reverse=True):
            print('{task_name}: {reward}'.format(task_name=task, reward=r), file=fout)
        print('* Total time per task', file=fout)
        for task, t in sorted(session.get_task_time().items(), key=operator.itemgetter(1)):
            print('{task_name}: {time}'.format(task_name=task, time=t), file=fout)
        print('* Number of trials per task', file=fout)
        for task, r in sorted(session.get_task_count().items(), key=operator.itemgetter(1)):
            print('{task_name}: {reward}'.format(task_name=task, reward=r), file=fout)


def setup_logging(default_path='logging.ini', default_level=logging.INFO, env_key='LOG_CFG'):
    """ Setup logging configuration
    
    :param default_path: 
    :param default_level: 
    :param env_key: 
    :return: 
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        logging.config.fileConfig(default_path)
    else:
        logging.basicConfig(level=default_level)

if __name__ == '__main__':
    main()
