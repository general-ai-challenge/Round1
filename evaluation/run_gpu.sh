#!/bin/bash
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



echo "Loading image, it may take a while..."
gunzip -c learner.tar.gz | docker load || exit 1

echo "Running the image..."
nvidia-docker run -d --user 1000:1000 --network=challengenetwork learner

