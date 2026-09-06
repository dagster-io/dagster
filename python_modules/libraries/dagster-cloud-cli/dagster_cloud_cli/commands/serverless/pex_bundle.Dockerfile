# Bundles a customer's PEX build (deps.pex + source.pex) into a standard Docker image by unpacking
# both into the image's DEFAULT site-packages (and /usr/local/bin) at build time. The running
# container is a normal pip-style layout with no PEX runtime, so the standard `dagster api grpc`
# code-server command works via the default interpreter — no reliance on custom PYTHONPATH/PATH
# (which the agent's code-server launch does not preserve).
#
# Built by _build_pex_docker_bundle (commands/ci/__init__.py) with --build-arg PYTHON_VERSION and a
# build context containing deps-*.pex and source-*.pex.
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim
ARG PYTHON_VERSION

RUN pip install --no-cache-dir pex

COPY deps-*.pex source-*.pex /pexes/

RUN set -eux; \
    pex-tools /pexes/deps-*.pex venv /tmp/deps --collisions-ok --non-hermetic-scripts --pip; \
    pex-tools /pexes/source-*.pex venv /tmp/source --collisions-ok --non-hermetic-scripts --pip; \
    sp="/usr/local/lib/python${PYTHON_VERSION}/site-packages"; \
    cp -a "/tmp/deps/lib/python${PYTHON_VERSION}/site-packages/." "$sp/"; \
    cp -a "/tmp/source/lib/python${PYTHON_VERSION}/site-packages/." "$sp/"; \
    for d in /tmp/deps /tmp/source; do \
      for f in "$d"/bin/*; do \
        b="$(basename "$f")"; \
        case "$b" in python*|pip*|activate*|Activate*|pex|wheel) continue;; esac; \
        sed "1s|^#!.*|#!/usr/local/bin/python${PYTHON_VERSION}|" "$f" > /usr/local/bin/"$b"; \
        chmod +x /usr/local/bin/"$b"; \
      done; \
    done; \
    rm -rf /pexes /tmp/deps /tmp/source /root/.pex
