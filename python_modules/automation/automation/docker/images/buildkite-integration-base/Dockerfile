####################################################################################################
#
# DAGSTER INTEGRATION IMAGE Base
#
# We use this Dockerfile to build an image for our Buildkite CI/CD pipeline.
#
####################################################################################################
ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

LABEL maintainer="Elementl"

# Never prompts the user for choices on installation/configuration of packages
ENV DEBIAN_FRONTEND=noninteractive \
    TERM=linux

# Set correct locale first and install deps for installing debian packages
RUN apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
    apt-transport-https \
    curl \
    ca-certificates \
    gnupg2 \
    locales \
    lsb-release \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    JAVA_HOME=/docker-java-home \
    # This Java version is obtained by running:
    #   docker run -it python:3.8.1-slim-buster /bin/bash
    #   echo "deb http://http.us.debian.org/debian stretch main contrib non-free" > /etc/apt/sources.list.d/91-debian-stretch.list
    #   apt-get update -yqq
    #   apt-cache policy openjdk-8-jdk-headless
    JAVA_DEBIAN_VERSION=8u232-b09-1~deb9u1 \
    SBT_VERSION=1.2.8 \
    PYSPARK_VERSION=2.4.4 \
    KUBECTL_VERSION=v1.16.4 \
    KIND_VERSION=v0.8.1

# Install kubectl
RUN echo "--- \033[32m:k8s: Install kubectl\033[0m" \
    && curl -LO "https://storage.googleapis.com/kubernetes-release/release/$KUBECTL_VERSION/bin/linux/amd64/kubectl" \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl

# Install kind & helm
RUN echo "--- \033[32m:k8s: Install kind\033[0m" \
    && curl -L "https://github.com/kubernetes-sigs/kind/releases/download/$KIND_VERSION/kind-linux-amd64" -o ./kind \
    && chmod +x ./kind \
    && mv ./kind /usr/local/bin/kind \
    && echo "--- \033[32m:k8s: Install helm\033[0m" \
    && curl "https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3" | bash

# This installs Java 8 (required by pyspark) - see: http://bit.ly/2ZIuHRh
RUN set -ex \
    && echo "--- \033[32m:debian: Install Debian packages\033[0m" \
    # Add a simple script that can auto-detect the appropriate JAVA_HOME value based on whether the JDK
    # or only the JRE is installed
    && { \
    echo '#!/bin/sh'; \
    echo 'set -e'; \
    echo; \
    echo 'dirname "$(dirname "$(readlink -f "$(which javac || which java)")")"'; \
    } > /usr/local/bin/docker-java-home \
    && chmod +x /usr/local/bin/docker-java-home \
    # Do some fancy footwork to create a JAVA_HOME that's cross-architecture-safe
    && ln -svT "/usr/lib/jvm/java-8-openjdk-$(dpkg --print-architecture)" /docker-java-home \
    # Pull in debian stretch stable repo so we can still get openjdk-8 on buster
    && echo "deb http://http.us.debian.org/debian stretch main contrib non-free" > /etc/apt/sources.list.d/91-debian-stretch.list \
    # PostgreSQL debian repo so that we can install PG 11 on both stretch and buster
    && echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && curl -sS https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - \
    # Node JS
    && curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    # Add yarn repo
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    # Deal with slim variants not having man page directories (which causes "update-alternatives" to fail)
    && mkdir -p /usr/share/man/man1 \
    # Refresh apt
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
    # Install deps
    && apt-get install -yqq --no-install-recommends \
    build-essential \
    bzip2 \
    cron \
    g++ \
    gcc \
    git \
    # These three packages are needed for Python 3.8 until the associated libraries publish wheels
    libc-dev \
    libgeos-dev \
    libpq-dev \
    make \
    nodejs \
    openjdk-8-jdk-headless="$JAVA_DEBIAN_VERSION" \
    openjdk-8-jre-headless="$JAVA_DEBIAN_VERSION" \
    pandoc \
    rabbitmq-server \
    rsync \
    ssh \
    software-properties-common \
    # Manually installing sudo else apt-get autoremove will fail trying to remove sudo later
    sudo \
    unzip \
    xz-utils \
    yarn \
    # Need to ensure PG installs from PG debian repo
    && apt-get install -yqq postgresql-11 -t "$(lsb_release -cs)-pgdg" \
    # update-alternatives so that future installs of other OpenJDK versions don't change /usr/bin/java
    && update-alternatives --get-selections | awk -v home="$(readlink -f "$JAVA_HOME")" 'index($3, home) == 1 { $2 = "manual"; print | "update-alternatives --set-selections" }' \
    # Validate installation
    && [ "$(readlink -f "$JAVA_HOME")" = "$(docker-java-home)" ] \
    && update-alternatives --query java | grep -q 'Status: manual' \
    && java -version


# Add files needed for build
ADD scala_modules scala_modules

# Add gcloud CLI debian pkg source
RUN echo "--- \033[32m:linux: Misc installs and cleanup\033[0m" \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - \
    # Install docker-compose
    && curl -L "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    && curl -fsSL "https://download.docker.com/linux/ubuntu/gpg" | apt-key add - \
    # Add SBT debian pkg
    && curl -LO "https://dl.bintray.com/sbt/debian/sbt-$SBT_VERSION.deb" \
    && dpkg -i sbt-$SBT_VERSION.deb \
    && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
    && apt-get -yqq update \
    && apt-get -yqq install \
    docker-ce \
    google-cloud-sdk \
    sbt \
    # Clean up after install process
    && apt-get remove -yqq \
    libgeos-dev \
    libpq-dev \
    # Validate that SBT works
    && sbt sbtVersion \
    # Pre-load jars for scala_modules by running a compile
    && cd /scala_modules \
    && make compile \
    && rm -rf /scala_modules \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
    /sbt-$SBT_VERSION.deb \
    /var/lib/apt/lists/* \
    /tmp/* \
    /var/tmp/* \
    /usr/share/doc \
    /usr/share/doc-base

# install git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get remove -yqq && \
    apt-get autoremove -yqq --purge && \
    apt-get clean

# pip install all of our deps to speed up our CI jobs
RUN pip install -U pip setuptools wheel \
    && pip install \
    awscli \
    pipenv

ENV PYSPARK_VERSION=2.4.4

# This will frequently OOM without --no-cache-dir
RUN echo "--- \033[32m:python: Install Python PySpark\033[0m" \
    && pip --no-cache-dir install pyspark==$PYSPARK_VERSION

ADD trigger_maven.py .

# This instigates some package downloads required by the airline-demo. Fails on Python 3.8
RUN python trigger_maven.py; rm trigger_maven.py; exit 0
