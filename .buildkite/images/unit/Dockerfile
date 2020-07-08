####################################################################################################
#
# DAGSTER UNIT IMAGE
#
# We use this Dockerfile to build an unit test image for our Buildkite CI/CD pipeline.
#
####################################################################################################

ARG BASE_IMAGE 
ARG PYTHON_VERSION
FROM "${BASE_IMAGE}"

RUN apt-get update -y \
    && apt-get install -y cron \
    && apt-get remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean

ADD snapshot-reqs-$PYTHON_VERSION.txt /snapshot-reqs.txt

RUN pip install -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt