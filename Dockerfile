FROM python:3.10-slim

# All packages are hard-pinned to `dagster`, so setting the version on just `DAGSTER` will ensure
# compatible versions.
RUN pip install -U uv
WORKDIR /dagster/python_modules
COPY python_modules/ .
WORKDIR /dagster
RUN python -m uv pip install \
    -e python_modules/dagster \
    -e python_modules/libraries/dagster-azure \
    -e python_modules/libraries/dagster-postgres \
    -e python_modules/libraries/dagster-aws \
    -e python_modules/libraries/dagster-celery[flower,redis,kubernetes] \
    -e python_modules/libraries/dagster-gcp \
    -e python_modules/dagster-graphql \
    -e python_modules/dagster-webserver
RUN python -m uv pip install \
    -e python_modules/libraries/dagster-celery-k8s \
    -e python_modules/libraries/dagster-k8s



COPY workspace.yaml /opt/dagster/app/workspace.yaml
COPY dagster.yaml /opt/dagster/dagster_home/dagster.yaml
COPY example_project /workspaces/example_project
# For python path correctness
ENV PYTHONPATH="/workspaces/:$PYTHONPATH"
