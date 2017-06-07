#!/bin/bash

cd agent

bash build.sh

cd ..

docker build -t learner . || exit 1

echo "Saving and compressing the image, it may take a while..."
docker save learner | gzip -c > learner.tar.gz

