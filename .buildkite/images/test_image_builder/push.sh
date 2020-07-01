#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
cd $ROOT/.buildkite/images/test_image_builder/
set -eux

TAG=`date '+%Y-%m-%d'`

echo -e "--- \033[32m:docker: Tag and push Docker images\033[0m"

# Log into ECR
aws ecr get-login --no-include-email --region us-west-1 | sh

docker tag "dagster/test-image-builder:v2" \
    "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/test-image-builder:v2"

docker push "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/test-image-builder:v2"