# -*- coding: utf-8
#
# Copyright (c) 2017, Stephen B, Hope,  All rights reserved.
#
# CommAI-env Copyright (c) 2016-present, Facebook, Inc., All rights reserved.
# Round1 Copyright (c) 2017-present, GoodAI All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE_CHALLENGE file in the root directory of this source tree.

FROM ubuntu

RUN apt-get update && apt-get install -y libzmq1

WORKDIR /app

ADD agent/example_learner /app/

ENV NAME Learner

CMD ["./example_learner"]

