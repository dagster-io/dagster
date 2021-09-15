####################################################################################################
#
# DAGSTER INTEGRATION IMAGE Base
#
# We use this Dockerfile to build an image for our Buildkite CI/CD pipeline.
# System dependencies go here - Python dependencies go in buildkite-integration.
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
    DOCKER_COMPOSE_VERSION=1.29.1 \
    KIND_VERSION=v0.9.0 \
    KUBECTL_VERSION=v1.20.1 \
    PYSPARK_VERSION=3.0.1 \
    SBT_VERSION=1.4.6 \
    FOSSA_VERSION=v1.1.10

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
RUN echo "--- \033[32m:debian: Install Debian packages\033[0m" \
    # Node JS
    && curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    # Add yarn repo
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    # Deal with slim variants not having man page directories (which causes "update-alternatives" to fail)
    && mkdir -p /usr/share/man/man1 /usr/share/man/man2 \
    && apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
    build-essential \
    bzip2 \
    cron \
    g++ \
    gcc \
    git \
    make \
    nodejs \
    openjdk-11-jdk-headless \
    openjdk-11-jre-headless \
    pandoc \
    postgresql \
    rabbitmq-server \
    rsync \
    ssh \
    software-properties-common \
    unzip \
    wget \
    xz-utils \
    yarn \
    # Confirm Java works
    && java -version


# Add files needed for build
ADD scala_modules scala_modules

# Add gcloud CLI debian pkg source
RUN echo "--- \033[32m:linux: Misc installs and cleanup\033[0m" \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - \
    # Install docker-compose
    && curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    && curl -fsSL "https://download.docker.com/linux/ubuntu/gpg" | apt-key add - \
    # Add SBT debian pkg
    && curl -LO "https://repo.scala-sbt.org/scalasbt/debian/sbt-$SBT_VERSION.deb" \
    && dpkg -i sbt-$SBT_VERSION.deb \
    && add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
    && apt-get -yqq update \
    && apt-get -yqq install \
    docker-ce \
    google-cloud-sdk \
    sbt \
    # Clean up after install process
    && apt-get remove -yqq \
    # Validate that SBT works
    && sbt sbtVersion -Dsbt.rootdir=true \
    # Pre-load jars for scala_modules by running a compile
    && cd /scala_modules \
    && make compile \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf \
        /scala_modules \
        /sbt-$SBT_VERSION.deb \
        /var/lib/apt/lists/* \
        /tmp/* \
        /var/tmp/* \
        /usr/share/doc \
        /usr/share/doc-base

# Install docker compose-cli
# https://github.com/docker/compose-cli/blob/main/INSTALL.md
RUN curl -L https://raw.githubusercontent.com/docker/compose-cli/main/scripts/install/install_linux.sh | sh

# Install Python deps
ADD trigger_maven.py .
RUN pip install -U pip setuptools wheel \
    && pip install \
        awscli \
        pipenv \
    && pip --no-cache-dir install pyspark==$PYSPARK_VERSION \
    # This instigates some package downloads required by the airline-demo
    && python trigger_maven.py \
    && rm trigger_maven.py

RUN wget http://download.redis.io/redis-stable.tar.gz \
    && tar xvzf redis-stable.tar.gz \
    && cd redis-stable \
    && make install

# Install FOSSA cli for analyzing our open-source dependencies
# https://github.com/fossas/fossa-cli
RUN curl -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/fossas/fossa-cli/master/install.sh | sh -s $FOSSA_VERSION

# Install libxmlsec to use xmlsec
RUN apt-get update -yqq \
    && apt-get upgrade -yqq \
    && apt-get install -yqq --no-install-recommends \
    libxmlsec1-dev \
    pkg-config
