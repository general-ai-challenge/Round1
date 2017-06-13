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

import json
import os


class JSONConfigLoader:
    """
    Loads a set of tasks and a schedule for them from a JSON file::

        {
          "tasks":
          {
            "<task_id>": {
                "type": "<task_class>",
            },
            "<task_id>": {
                "type": "<task_class>",
                "world": "<world_id>"
            }
            "...": "..."
          },
          "worlds":
          {
            "<world_id>": {
              "type": "<world_class>",
            }
          },
          "scheduler":
            {
              "type": "<scheduler_class>",
              "args": {
                  "<scheduler_arg>": <scheduler_arg_value>,
                }
            }
        }

    The scheduler scheduler_arg_value could be a container including
    task ids, which will be replaced by the concrete tasks instances.
    """
    def create_tasks(self, tasks_config_file):
        """Given a json configuartion file, it returns a scheduler object set up as described in the file. instantiate
        the worlds (typically there is only one) map each task,  instantiate the tasks with the world (if any)
        retrieve what type of scheduler we need to create.  prepare the arguments to instantiate the scheduler.
         all arguments that begin with the name tasks are taken as collections of ids that should be mapped to the
         corresponding tasks object.  return a scheduler with its corresponding arguments

        :param tasks_config_file:
        :return:
        """
        config = json.load(open(tasks_config_file))
        worlds = dict((world_id, self.instantiate_world(world_config['type']))
                      for world_id, world_config in config['worlds'].items())
        tasks = dict((task_id, self.instantiate_task(task_config['type'], worlds, task_config.get('world', None)))
                      for task_id, task_config in config['tasks'].items())
        scheduler_class = get_class(config['scheduler']['type'])
        scheduler_args = {}
        for arg_name, arg_value in config['scheduler']['args'].items():
            if arg_name.startswith('tasks'):
                scheduler_args[arg_name] = map_tasks(arg_value, tasks)
            else:
                scheduler_args[arg_name] = arg_value
        return scheduler_class(**scheduler_args)

    def instantiate_world(self, world_class):
        """ Return a world object given the world class

        :param world_class:
        :return:
        """
        C = get_class(world_class)
        try:
            return C()
        except Exception as e:
            raise RuntimeError("Failed to instantiate world {0} ({1})".format(world_class, e))

    def instantiate_task(self, task_class, worlds, world_id=None):
        """ Returns a task object given the task class and the world where it runs (if any)

        :param task_class:
        :param worlds:
        :param world_id:
        :return:
        """
        C = get_class(task_class)
        try:
            if world_id:
                return C(worlds[world_id])
            else:
                return C()
        except Exception as e:
            raise RuntimeError("Failed to instantiate task {0} ({1})".format(task_class, e))


class PythonConfigLoader:
    """
     Loads a python file containing a stand-alone function called `create_tasks` that returns a TaskScheduler object.
    """

    def create_tasks(self, tasks_config_file):
        """ make sure we have a relative path.  just in case, remove initial unneeded "./" transform the config file
        path into a module path

        :param tasks_config_file:
        :return:
        """
        tasks_config_file = os.path.relpath(tasks_config_file)
        if tasks_config_file.startswith('..'):
            raise RuntimeError("The task configuration file must be in the "
                               "same directory as the competition source.")
        if tasks_config_file.startswith('./'):
            tasks_config_file = tasks_config_file[2:]
        tasks_config_module = os.path.splitext(
            tasks_config_file)[0].replace('/', '.')
        mod = __import__(tasks_config_module, fromlist=[''])
        return mod.create_tasks()


def get_class(name):
    """

    :param name:
    :return:
    """
    components = name.split('.')
    mod = __import__('.'.join(components[:-1]), fromlist=[components[-1]])
    mod = getattr(mod, components[-1])
    return mod


def map_tasks(arg, tasks):
    """ if arg is a task, return the task object.  arg is a hashable type, but we cannot map it to a task.
    unhashable type we treat arg as a collection that should be mapped

    :param arg:
    :param tasks:
    :return:
    """
    try:
        return tasks[arg]
    except KeyError:
        raise RuntimeError("Coudln't find task id '{0}'.".format(arg))
    except TypeError:
        return list(map(lambda x: map_tasks(x, tasks), arg))
