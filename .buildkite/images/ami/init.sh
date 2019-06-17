#!/bin/bash
echo "downloading dagster build images..."

docker pull dagster/buildkite-integration:py3.7.3-v4
docker pull dagster/buildkite-integration:py3.6.8-v4
docker pull dagster/buildkite-integration:py3.5.7-v4
docker pull dagster/buildkite-integration:py2.7.16-v4
