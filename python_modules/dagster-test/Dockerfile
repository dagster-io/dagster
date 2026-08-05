ARG BASE_IMAGE
ARG PYTHON_VERSION

FROM "${BASE_IMAGE}"

COPY modules /modules
COPY dagster_test /modules/dagster-test/dagster_test
COPY pyproject.toml /modules/dagster-test/pyproject.toml

ENV GOOGLE_APPLICATION_CREDENTIALS="/modules/gac.json"

ENV DAGSTER_DISABLE_TELEMETRY=true

# This makes sure that logs show up immediately instead of being buffered
ENV PYTHONUNBUFFERED=1

RUN pip install -U uv

# `--no-sources` is required because each module's pyproject.toml now has
# `[tool.uv.sources]` pointing to relative sibling paths (e.g.
# `dagster-pipes = { path = "../dagster-pipes", editable = true }`) for the
# per-package lockfile workflow. With `uv pip install`, uv resolves those
# paths relative to the current working directory rather than the
# pyproject's location, producing bogus targets like `file:///dagster`.
# Disabling sources tells uv to treat each `[project].dependencies` entry
# as a normal registry spec; the explicit `-e /modules/...` entries below
# already provide the local editable installs.
RUN python -m uv pip install --no-sources \
    -e /modules/dagster \
    -e /modules/dagster-graphql \
    -e /modules/dagster-celery[flower,redis,kubernetes] \
    -e /modules/dagster-webserver \
    -e /modules/dagster-postgres \
    -e /modules/dagster-pandas \
    -e /modules/dagster-aws \
    -e /modules/dagster-gcp \
    -e /modules/dagster-k8s \
    -e /modules/dagster-celery-k8s \
    -e /modules/dagster-celery-docker \
    -e /modules/dagster-docker \
    -e /modules/dagster-airflow \
    -e /modules/dagstermill \
    -e /modules/dagster-pipes \
    -e /modules/dagster-shared \
    -e /modules/dagster-test


RUN ! (pip list --exclude-editable | grep -e dagster)

WORKDIR /modules/dagster-test/dagster_test/test_project/

EXPOSE 80
