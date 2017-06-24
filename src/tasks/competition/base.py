# -*- coding: utf-8
# 'version': '0.3'
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.
# TODO task unresolved ref
from core.task import Task, on_message


class BaseTask(Task):
    """
      Base task for other tasks in the competition implementing behaviour that should be shared by most of the tasks.
    """

    def __init__(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        """
        super(BaseTask, self).__init__(*args, **kwargs)

    @on_message('.')
    def on_any_message(self, event):
        """  # ignore anything the learner says while the teacher is speaking # if the environment is speaking
          # and the last message was not a silence  # i will ignore what the learner just said by forgetting it

        :param event:
        :return:
        """
        if not self._env.is_silent():
            if event.message[-1] != ' ':
                self.ignore_last_char()
