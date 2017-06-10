# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

from core.task import Task, on_message


class BaseTask(Task):
    '''
    Base task for other tasks in the competition implementing
    behaviour that should be shared by most of the tasks.
    '''

    def __init__(self, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)

    # ignore anything the learner says while the teacher is speaking
    @on_message('.')
    def on_any_message(self, event):
        # if the environment is speaking
        if not self._env.is_silent():
            # and the last message was not a silence
            if event.message[-1] != ' ':
                # i will ignore what the learner just said by forgetting it
                self.ignore_last_char()
