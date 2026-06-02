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

LABEL maintainer="Dagster Labs"

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

# Envionment variables that will be referenced during installation of various packages
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    KIND_VERSION=v0.14.0 \
    KUBECTL_VERSION=v1.31.2 \
    HELM_VERSION=v3.20.2 \
    FOSSA_VERSION=3.17.2 \
    AWSCLI_VERSION=2.34.38

# Install Kubernetes tools: kubectl, kind, helm
RUN curl --fail -LO "https://dl.k8s.io/release/$KUBECTL_VERSION/bin/linux/amd64/kubectl" \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl \
    && curl --fail -L "https://github.com/kubernetes-sigs/kind/releases/download/$KIND_VERSION/kind-linux-amd64" -o ./kind \
    && chmod +x ./kind \
    && mv ./kind /usr/local/bin/kind \
    && curl --fail -LO "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" \
    && tar -zxvf "helm-${HELM_VERSION}-linux-amd64.tar.gz" \
    && mv linux-amd64/helm /usr/local/bin/helm \
    && rm -rf linux-amd64 "helm-${HELM_VERSION}-linux-amd64.tar.gz"

# Install libxmlsec to use xmlsec and libffi for cffi
RUN apt-get update -yqq \
    && apt-get install -yqq --no-install-recommends \
    libffi-dev \
    libxmlsec1-dev \
    pkg-config

# Install Java (required by pyspark) - Java 17 for compatibility with both Spark 3 and 4
COPY --from=eclipse-temurin:17-jdk-jammy /opt/java/openjdk /opt/java/openjdk
ENV JAVA_HOME /opt/java/openjdk
RUN update-alternatives --install /usr/bin/java java /opt/java/openjdk/bin/java 1

# Install various packages used in running/installing/testing Dagster:
# - git/just (cloning dagster, running checks)
# - nodejs/yarn (dagster UI)
# - assorted others-- some may no longer be required, but leaving in place for now
#
# deb.nodesource script adds node source to apt
RUN curl -sL https://deb.nodesource.com/setup_22.x | bash - \
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
    pandoc \
    postgresql \
    rabbitmq-server \
    rsync \
    ssh \
    unzip \
    wget \
    xz-utils \
    yarn

# Install FOSSA cli for analyzing our open-source dependencies
# https://github.com/fossas/fossa-cli
RUN wget https://github.com/fossas/fossa-cli/releases/download/v${FOSSA_VERSION}/fossa_${FOSSA_VERSION}_linux_amd64.tar.gz \
    && tar xvzf fossa_${FOSSA_VERSION}_linux_amd64.tar.gz fossa \
    && chmod +x ./fossa \
    && mv ./fossa /usr/local/bin/fossa \
    && rm fossa_${FOSSA_VERSION}_linux_amd64.tar.gz \
    && fossa --version

# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install#deb
# Add Google Cloud GPG key and apt source (using modern method without deprecated apt-key)
RUN curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
    gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
    tee -a /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null \
    && apt-get -yqq update \
    && apt-get -yqq install \
    google-cloud-cli

# Install Docker
# See: https://docs.docker.com/engine/install/debian/
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | \
    gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | \
    tee -a /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get -yqq update \
    && apt-get -yqq install \
    docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /bin/

# Install just (task runner-- replaces make for CI steps because it propagates
# signal exit codes correctly, enabling Buildkite automatic retry on spot
# reclamation)
RUN apt-get update -yqq && apt-get install -yqq just

# Install redis
ENV REDIS_VERSION=7.4.8
RUN wget https://download.redis.io/releases/redis-${REDIS_VERSION}.tar.gz \
    && tar xvzf redis-${REDIS_VERSION}.tar.gz \
    && cd redis-${REDIS_VERSION} \
    && make install

# Install the DuckDB CLI
ENV DUCKDB_VERSION=v1.5.2
RUN curl --fail --silent --show-error --location \
    --output duckdb_cli-linux-amd64.zip \
    https://github.com/duckdb/duckdb/releases/download/${DUCKDB_VERSION}/duckdb_cli-linux-amd64.zip \
    && unzip duckdb_cli-linux-amd64.zip \
    && mv duckdb /usr/local/bin/duckdb \
    && chmod +x /usr/local/bin/duckdb

# Install AWS CLI v2 (ships as a standalone binary, not on PyPI)
RUN curl --fail --silent --show-error --location \
    --output /tmp/awscliv2.zip \
    "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWSCLI_VERSION}.zip" \
    && unzip -q /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/awscliv2.zip /tmp/aws

# AWS CLI v2 pages output through `less` by default; this image has no `less`,
# so without this every `aws` invocation fails with exit 253.
ENV AWS_PAGER=""

# Clean up
RUN apt-get remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean

# Temp image used to get non-dagster Python dependencies
FROM system_base AS snapshot_builder

# Build a requirements file with all non-Dagster packages that are dependencies of a Dagster
# package.
RUN git clone --depth 1 https://github.com/dagster-io/dagster.git

WORKDIR dagster

ENV VIRTUAL_ENV=/usr/local
ENV UV_HTTP_TIMEOUT=300
RUN python scripts/install_dev_python_modules.py --system || exit 1
RUN uv pip freeze --exclude-editable > /snapshot-reqs.txt

# Final image includes both system deps and preinstalled non-Dagster python deps
FROM system_base

COPY --from=snapshot_builder /snapshot-reqs.txt .

# Configure uv cache + link behavior up front, so it applies to the
# snapshot preinstall below as well as to runtime CI invocations.
#
# UV_CACHE_DIR=/work/.cache/uv — set here (not at the end of the
# Dockerfile) so the snapshot wheels installed below land at the runtime
# cache path. Without this, uv defaults to /root/.cache/uv during image
# build while runtime looks at /work/.cache/uv, so the snapshot never
# serves as a cache hit and every CI venv re-downloads from PyPI.
#
# UV_LINK_MODE=symlink — at runtime the cache lives on the container
# overlay (/work) while target venvs typically live on a bind-mounted
# host path (e.g. /workdir under the docker plugin). uv's default
# hardlink mode fails across filesystems and falls back to full copies,
# doubling the wheel footprint on a single underlying volume — enough
# on heavy steps like rebuild_pyright_pins (810 wheels, including CUDA
# libs) to ENOSPC a 16 GB agent volume. Symlinks cross filesystems
# freely and add ~0 bytes to the venv. Setting it here means the
# snapshot install also uses symlinks: system site-packages becomes
# symlinks pointing into /work/.cache/uv, which we keep around for
# runtime anyway, so this is fine.
ENV UV_CACHE_DIR=/work/.cache/uv \
    UV_LINK_MODE=symlink

# Preinstall non-Dagster packages in image so that the virtual environment
# builds faster in Buildkite. Seeds /work/.cache/uv with extracted wheels
# which runtime venvs symlink from.
RUN uv pip install --system -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt

# New versions of debian require allowlisting folders where `git` can run
RUN git config --system --add safe.directory \*

# Open up root-owned locations that CI writes to at runtime, so they remain
# writable when the container runs as a non-root UID.
#
# When the docker plugin runs this image with `propagate-uid-gid: true`, the
# container runs as the host buildkite-agent UID (e.g. 2000). That UID has no
# /etc/passwd entry inside the container, so it has no group memberships beyond
# the primary one and cannot write to root-owned paths with the default 755/644
# permissions. CI exercises several such paths at runtime:
#
#   - `uv pip install --system ...` writes packages into
#     /usr/local/lib/python3.12/site-packages and entry-point scripts into
#     /usr/local/bin (e.g. `dagster-labs image sync-aws` reinstalls
#     automation-internal this way).
#   - `npm install -g ...` writes modules into /usr/lib/node_modules and links
#     binaries into /usr/local/bin (e.g. `prettier` for lint steps).
#   - `git config --system ...` writes to /etc/gitconfig (created above by the
#     `safe.directory` line, so it exists with mode 644 and is read-only for
#     non-root from then on).
#
# `chmod -R a+w` grants write to all users on these trees. It is a blunt
# instrument — any process in the container can modify these locations — but
# the image is ephemeral and single-tenant per CI job, so there is no
# meaningful security boundary to preserve. Tightening this (e.g. via a shared
# group) would add complexity without buying anything in this environment.
#
# /usr/local/lib recursively covers the python site-packages directory, so it
# does not need to be listed separately.
RUN chmod -R a+w /usr/local/lib /usr/local/bin /usr/lib/node_modules \
    && chmod a+w /etc/gitconfig

# Provide a writable HOME and cache dirs that work for any UID at runtime.
# When the docker plugin runs this image with `propagate-uid-gid: true`, the
# container runs as the host buildkite-agent UID — which has no /etc/passwd
# entry inside the container, so $HOME would otherwise default to / (read-only).
# A sticky world-writable /work lets uv/pip/etc. write per-user state regardless
# of which UID the container ends up running as.
RUN mkdir -p /work/.cache && chmod -R 1777 /work
ENV HOME=/work \
    XDG_CACHE_HOME=/work/.cache
