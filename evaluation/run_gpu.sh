#!/bin/bash

gunzip -c learner.tar.gz | docker load
nvidia-docker run -d --user 1000:1000 --network=challengenetwork learner

