FROM python:3.14.6-slim-bookworm@sha256:4c92ffcde4dd6f1ff72a24518f49fd4990b27134987dfa31a733badde66df9f8 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.23@sha256:d0a0a753ab981624b49c97abc98821c1c09f4ca69d1ef5cee69c501be3d88479 /uv /bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1
RUN uv --no-config venv --python /usr/local/bin/python /opt/venv
COPY dependency-constraints.txt /tmp/dependency-constraints.txt
COPY runtime-requirements.txt /tmp/runtime-requirements.txt
COPY packages /packages
# Preserve upstream's .gitignore with source packages: Hatch's force-include of
# dagster/_core/definitions/tags compensates for that ignore rule. Without it,
# Hatch adds those files twice and rejects the duplicate wheel archive path.
RUN --mount=type=cache,target=/root/.cache/uv uv --no-config pip install \
    --no-sources --no-editable --python /opt/venv/bin/python \
    -c /tmp/dependency-constraints.txt -r /tmp/runtime-requirements.txt /packages/*

FROM python:3.14.6-slim-bookworm@sha256:4c92ffcde4dd6f1ff72a24518f49fd4990b27134987dfa31a733badde66df9f8
COPY --from=builder /opt/venv /opt/venv
COPY cancel_k8s_fixture.py k8s_cancel_probe.py /opt/probe/
ENV PATH=/opt/venv/bin:$PATH PYTHONPATH=/opt/probe PYTHONUNBUFFERED=1
WORKDIR /opt/probe
