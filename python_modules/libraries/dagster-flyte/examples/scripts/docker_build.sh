#!/usr/bin/env bash

# WARNING: THIS FILE IS MANAGED IN THE 'BOILERPLATE' REPO AND COPIED TO OTHER REPOSITORIES.
# ONLY EDIT THIS FILE FROM WITHIN THE 'LYFT/BOILERPLATE' REPOSITORY:
#
# TO OPT OUT OF UPDATES, SEE https://github.com/lyft/boilerplate/blob/master/Readme.rst

set -e

echo ""
echo "------------------------------------"
echo "           DOCKER BUILD"
echo "------------------------------------"
echo ""

if [ -n "$REGISTRY" ]; then
  # Do not push if there are unstaged git changes
  CHANGED=$(git status --porcelain)
  if [ -n "$CHANGED" ]; then
    echo "Please commit git changes before pushing to a registry"
    exit 1
  fi
fi

GIT_SHA=$(git rev-parse HEAD)

IMAGE_TAG="${CONTAINER_REGISTRY}:latest"

# build the image
docker build -t "$IMAGE_TAG" --build-arg IMAGE_TAG="${IMAGE_TAG}" \
 --build-arg PYTHON_VERSION="${PYTHON_VERSION}" .

# uncomment for actual use
# docker push ${CONTAINER_REGISTRY}:latest

echo "${IMAGE_TAG} built locally."
