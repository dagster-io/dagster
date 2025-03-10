#!/bin/bash

set -eu

echo "Pruning docker containers..."
CONTAINERS=$(docker ps --all --quiet)
if [ "$CONTAINERS" ]; then
  docker stop $CONTAINERS
  docker container prune --force
fi
echo "Pruning docker networks..."
docker network prune --force
