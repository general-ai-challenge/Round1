#!/bin/bash

echo "Loading image, it may take a while..."
gunzip -c learner.tar.gz | docker load || exit 1

echo "Running the image..."
nvidia-docker run -d --user 1000:1000 --network=challengenetwork learner

