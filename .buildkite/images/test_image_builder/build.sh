#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
cd $ROOT/.buildkite/images/test_image_builder/
set -eux

docker build . -t dagster/test-image-builder:v2