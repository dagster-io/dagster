#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
cd $ROOT/.buildkite/images/integration/
set -eux

if [ "$#" -ne 2 ]; then
    echo "Error: Must specify a Python version and image version.\n" 1>&2
    echo "Usage: ./push.sh 3.7.4 v6" 1>&2
    exit 1
fi

# e.g. 3.7.4
PYTHON_VERSION=$1
# e.g. 3
PYTHON_MAJOR_VERSION="${PYTHON_VERSION:0:1}"
# e.g. 37
PYTHON_MAJMIN=`echo "${PYTHON_VERSION:0:3}" | sed 's/\.//'`

# Version of the buildkite integration image
IMAGE_VERSION=$2

TAG=`date '+%Y-%m-%d'`

echo -e "--- \033[32m:docker: Tag and push Docker images\033[0m"

# Log into ECR
aws ecr get-login --no-include-email --region us-west-1 | sh

docker tag "dagster/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}" \
    "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}"

docker push "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}"
