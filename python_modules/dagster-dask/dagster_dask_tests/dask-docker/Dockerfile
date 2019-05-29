ARG PYTHON_VERSION

FROM python:$PYTHON_VERSION

ADD dagster dagster
ADD dagster-graphql dagster-graphql
ADD dagster-dask dagster-dask
ADD dagster-aws dagster-aws
ADD examples examples

RUN pip install -e dagster/
RUN pip install -e dagster-graphql/
RUN pip install -e dagster-dask/
RUN pip install -e dagster-aws/
RUN pip install -e examples/
