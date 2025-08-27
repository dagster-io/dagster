#!/bin/bash

set -eu

if [ -n "${BUILDKITE:-}" ]; then
  if [ -n "${KUBERNETES_PORT-}" ]; then
    echo "don't docker prune, we're running in kubernetes"
  else
    echo "Pruning docker containers..."
    CONTAINERS=$(docker ps --all --quiet)
    if [ "$CONTAINERS" ]; then
      docker stop $CONTAINERS
      docker container prune --force
    fi
    echo "Pruning docker networks..."
    docker network prune --force
  fi
fi
