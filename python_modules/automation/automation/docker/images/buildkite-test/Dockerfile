####################################################################################################
#
# DAGSTER BUILDKITE TEST
#
# This Dockerfile specifies an image that serves as base for all Python testing
# steps (both integration and unit) run on BK. 
#
####################################################################################################
ARG BASE_IMAGE
FROM "${BASE_IMAGE}" AS system_base

LABEL maintainer="Elementl"

# Never prompts the user for choices on installation/configuration of packages (NOTE:
# DEBIAN_FRONTEND does not affect the apt-get command)
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
    # Set locale
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
    FOSSA_VERSION=v1.1.10

# Install kubectl
RUN curl -LO "https://storage.googleapis.com/kubernetes-release/release/$KUBECTL_VERSION/bin/linux/amd64/kubectl" \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl

# Install kind & helm
RUN curl -L "https://github.com/kubernetes-sigs/kind/releases/download/$KIND_VERSION/kind-linux-amd64" -o ./kind \
    && chmod +x ./kind \
    && mv ./kind /usr/local/bin/kind \
    && echo "--- \033[32m:k8s: Install helm\033[0m" \
    && curl "https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3" | bash

# Install libxmlsec to use xmlsec
RUN apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
       libxmlsec1-dev \
       pkg-config

# Install Java 8 (required by pyspark) - see: http://bit.ly/2ZIuHRh
# nodejs
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    # Add yarn GPG key and apt source
    && curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | \
       gpg --dearmor -o /usr/share/keyrings/yarnkey.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/yarnkey.gpg] https://dl.yarnpkg.com/debian/ stable main" | \
       tee -a /etc/apt/sources.list.d/yarn.list >/dev/null \
    # Deal with slim variants not having man page directories (which causes "update-alternatives" to fail)
    && mkdir -p /usr/share/man/man1 /usr/share/man/man2 \
    && apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
       build-essential \
       bzip2 \
       cron \
       g++ \
       gcc \
       git \
       make \
       mariadb-client \
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

# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install#deb
# Add Google Cloud GPG key and apt source
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg > /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
       tee -a /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null \
    # Install google cloud
    && apt-get -yqq update \
    && apt-get -yqq install \
       google-cloud-sdk

# Install Docker
# https://docs.docker.com/engine/install/debian/
# Add docker GPG key and apt source
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | \
       gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | \
       tee -a /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get -yqq update \
    && apt-get -yqq install \
       docker-ce \
    # Install docker-compose
    && curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose \
    # Install docker compose-cli
    # https://github.com/docker/compose-cli/blob/main/INSTALL.md
    && curl -L https://raw.githubusercontent.com/docker/compose-cli/main/scripts/install/install_linux.sh | sh

# Install Python build deps
RUN pip install -U pip setuptools wheel

# Install redis
RUN wget http://download.redis.io/redis-stable.tar.gz \
    && tar xvzf redis-stable.tar.gz \
    && cd redis-stable \
    && make install

# Install FOSSA cli for analyzing our open-source dependencies
# https://github.com/fossas/fossa-cli
RUN curl -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/fossas/fossa-cli/master/install.sh | \
       sh -s $FOSSA_VERSION

# Clean up
RUN apt-get remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean


# Temp image used to get non-dagster Python dependencies
FROM system_base AS snapshot_builder

# Build a requirements file with all non-Dagster packages that are dependencies of a Dagster
# package. We also install `awscli` (used in Buildkite) at this stage so that it can be installed
# together with Dagster dependencies. This allows pip's dependency resolver to account for
# everything.
RUN git clone https://github.com/dagster-io/dagster.git

WORKDIR dagster

RUN python scripts/install_dev_python_modules.py awscli \
    && pip freeze --exclude-editable > /snapshot-reqs.txt

# Final image includes both system deps and preinstalled non-Dagster python deps
FROM system_base

COPY --from=snapshot_builder /snapshot-reqs.txt .

# Preinstall non-Dagster packages in image so that the virtual environment
# builds faster in Buildkite.
RUN pip install -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt
