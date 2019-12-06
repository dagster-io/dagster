####################################################################################################
#
# DAGSTER BASE IMAGE
#
# We use this image to derive both an image for our Buildkite CI/CD pipeline, as well as a public
# Dagster image.
#
####################################################################################################
ARG DEBIAN_VERSION
ARG PYTHON_VERSION

FROM python:"${PYTHON_VERSION}-${DEBIAN_VERSION}" AS dagster-base-build-image

# ARG must be both before and after FROM
# See https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG DEBIAN_VERSION

LABEL maintainer="Elementl"

# Never prompts the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND noninteractive
ENV TERM linux

# Define en_US.
RUN apt-get update -yqq \
    && apt-get install -y locales \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure locales \
    && update-locale LANG=en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Set env vars
# This installs Java 8 (required by pyspark) - see: http://bit.ly/2ZIuHRh
ENV JAVA_HOME /docker-java-home
ENV JAVA_VERSION 8u222
ENV JAVA_DEBIAN_VERSION 8u222-b10-1~deb9u1
ENV SBT_VERSION=1.2.8
ENV PYSPARK_VERSION=2.4.4
ENV KUBECTL_VERSION=v1.16.3
ENV KIND_VERSION=v0.5.1

# add a simple script that can auto-detect the appropriate JAVA_HOME value
# based on whether the JDK or only the JRE is installed
RUN { \
		echo '#!/bin/sh'; \
		echo 'set -e'; \
		echo; \
		echo 'dirname "$(dirname "$(readlink -f "$(which javac || which java)")")"'; \
	} > /usr/local/bin/docker-java-home \
	&& chmod +x /usr/local/bin/docker-java-home \
    # do some fancy footwork to create a JAVA_HOME that's cross-architecture-safe
    && ln -svT "/usr/lib/jvm/java-8-openjdk-$(dpkg --print-architecture)" /docker-java-home \
    # Pull in debian stretch stable repo so we can still get openjdk-8 on buster
    && echo "APT::Default-Release \"stable\";" > /etc/apt/apt.conf.d/99defaultrelease \
    && echo "deb http://http.us.debian.org/debian stretch main contrib non-free" > /etc/apt/sources.list.d/91-debian-stretch.list

RUN set -ex \
    && curl -sL https://deb.nodesource.com/setup_11.x | bash - \
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
# Deal with slim variants not having man page directories (which causes "update-alternatives"
    && mkdir -p /usr/share/man/man1 \
# Refresh apt
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
# Install deps
    && apt-get install -yqq --no-install-recommends \
        bzip2 \
        cron \
        openjdk-8-jre-headless="$JAVA_DEBIAN_VERSION" \
        openjdk-8-jdk-headless="$JAVA_DEBIAN_VERSION" \
        nodejs \
        rsync \
        software-properties-common \
        unzip \
        xz-utils \
        yarn \
# Clean up after install process
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/doc \
        /usr/share/doc-base \
# update-alternatives so that future installs of other OpenJDK versions don't change /usr/bin/java
    && update-alternatives --get-selections | awk -v home="$(readlink -f "$JAVA_HOME")" 'index($3, home) == 1 { $2 = "manual"; print | "update-alternatives --set-selections" }' \
# Validate installation
    && [ "$(readlink -f "$JAVA_HOME")" = "$(docker-java-home)" ] \
    && update-alternatives --query java | grep -q 'Status: manual' \
    && java -version

# On buster, pyarrow wheels aren't available. Build from source.
ADD pyarrow-0.15.1.dev403+gfe41a6822-cp38-cp38-linux_x86_64.whl .
RUN if [ "${DEBIAN_VERSION}" = "buster" ]; then pip install pyarrow-0.15.1.dev403+gfe41a6822-cp38-cp38-linux_x86_64.whl; fi

# This will frequently OOM without --no-cache-dir
RUN pip --no-cache-dir install pyspark==$PYSPARK_VERSION

####################################################################################################
#
# DAGSTER PUBLIC IMAGE
#
####################################################################################################
FROM dagster-base-build-image AS dagster-public-image

RUN pip install -U pip setuptools wheel && \
    git clone https://github.com/dagster-io/dagster.git

WORKDIR /dagster/
RUN make dev_install


####################################################################################################
#
# DAGSTER BUILDKITE INTEGRATION IMAGE
#
####################################################################################################
FROM dagster-base-build-image AS dagster-integration-image
ARG PYTHON_MAJOR_VERSION

# This instigates some package downloads required by the airline-demo. Fails on Python 3.8
ADD trigger_maven.py .
RUN python trigger_maven.py; exit 0

RUN apt-get update -yqq \
    && apt-get install -yqq \
        libgdal-dev \
        libgeos-dev \
        libpq-dev

# pip install all the downstream deps to speed up our CI jobs
ADD snapshot-reqs-$PYTHON_MAJOR_VERSION.txt /snapshot-reqs.txt
RUN pip install -U pip setuptools wheel \
    && pip install tox \
    && pip install -r /snapshot-reqs.txt

# Install Docker and other dependencies
RUN curl -L "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    # Get SBT
    && curl -LO https://dl.bintray.com/sbt/debian/sbt-$SBT_VERSION.deb \
    && dpkg -i sbt-$SBT_VERSION.deb \
    && rm sbt-$SBT_VERSION.deb \
    && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
    && apt-get -yqq update \
    && apt-get -yqq install \
        apt-transport-https \
        ca-certificates \
        curl \
        docker-ce \
        gnupg2 \
        pandoc \
        sbt \
# Clean up after install process
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/doc \
        /usr/share/doc-base \
# Validate
    && sbt sbtVersion

# Install kubectl and kind CLI utils
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$KUBECTL_VERSION/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl \
    && curl -Lo ./kind https://github.com/kubernetes-sigs/kind/releases/download/$KIND_VERSION/kind-linux-amd64 \
    && chmod +x ./kind \
    && mv ./kind /usr/local/bin/kind

# Pre-load jars for scala_modules by running a compile
ADD scala_modules scala_modules
RUN cd scala_modules && make compile

# Final cleanup
RUN rm -rf /scala_modules \
    /snapshot-reqs.txt \
    /trigger_maven.py \
    /pyarrow-0.15.1.dev403+gfe41a6822-cp38-cp38-linux_x86_64.whl
