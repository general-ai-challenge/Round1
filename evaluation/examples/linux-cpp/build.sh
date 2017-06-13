#!/bin/bash
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

cd agent

bash make.sh

cd ..

docker build -t learner . || exit 1

echo "Saving and compressing the image, it may take a while..."
docker save learner | gzip -c > learner.tar.gz

