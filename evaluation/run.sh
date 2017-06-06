#!/bin/bash

gunzip -c learner.tar.gz | docker load
docker run -d --user 1000:1000 --network=challengenetwork learner

