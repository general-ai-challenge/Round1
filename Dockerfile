#!/usr/bin/env python3
# -*- coding: utf-8
# 'version': '0.3'
#
# Copyright (c) 2017-, Stephen B. Hope
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the LICENSE.md file in the root directory of this
# source tree. An additional grant of patent rights can be found in the PATENTS file in the same directory.

FROM python:3.5-slim
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80


ENV NAME Revised-Round1-CommAI-env

CMD ["python", "app.py"]