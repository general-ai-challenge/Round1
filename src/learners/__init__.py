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

# import all learners in the current directory
# adapted from: http://stackoverflow.com/a/1057534/367489
# FIXME: this architecture is probably fragile. Test where it fails and fix it.

from os.path import dirname, basename, isfile
import glob
modules = glob.glob(dirname(__file__) + "/*.py")
for m in [basename(f)[:-3] for f in modules if isfile(f)]:
    __import__('learners.' + m)
