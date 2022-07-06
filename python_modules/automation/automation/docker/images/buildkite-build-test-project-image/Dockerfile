####################################################################################################
#
# DAGSTER BUILDKITE TEST IMAGE BUILDER
#
# This Dockerfile specifies an image with a test Dagster project. It is built
# during every run of BK. The base image is `buildkite-test-image-builder-base`.
#
####################################################################################################
# This image is used to bootstrap the test image building process
ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

# Next two commands lifted from https://github.com/jpetazzo/dind/blob/master/Dockerfile

# Let's start with some basic stuff.
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    lxc \
    iptables

RUN curl -sSL https://get.docker.com/ > install_docker.sh

RUN pip install pex==2.1.12

ADD requirements.txt .

RUN pex -r requirements.txt -m awscli -o aws.pex

# Now we usage a multistage build to remove the cruft above
# that was needed to get the shell script

FROM "${BASE_IMAGE}"

WORKDIR /scriptdir

COPY --from=0 install_docker.sh .

COPY --from=0 aws.pex .

RUN sh install_docker.sh && \
    chmod +x aws.pex && \
    # Buildkite mounts the checkout to /workdir
    # Requires git in order to do that
    apt-get update && \
    apt-get install -y git rsync && \
    apt-get remove -yqq && \
    apt-get autoremove -yqq --purge && \
    apt-get clean && \
    rm install_docker.sh && \
    rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*
