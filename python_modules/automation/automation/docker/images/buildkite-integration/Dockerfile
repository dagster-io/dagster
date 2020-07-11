####################################################################################################
#
# DAGSTER INTEGRATION IMAGE
#
# We use this Dockerfile to build an image for our Buildkite CI/CD pipeline.
#
####################################################################################################

ARG BASE_IMAGE
ARG PYTHON_VERSION
FROM "${BASE_IMAGE}"

ADD snapshot-reqs-$PYTHON_VERSION.txt /snapshot-reqs.txt

RUN pip install -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt