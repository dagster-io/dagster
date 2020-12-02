FROM python:3.7-slim

# Install dagster from master (the public example won't need to do this, not sure how to navigate
# that)

WORKDIR /tmp

# Install git
RUN apt-get update && apt-get install -yqq git

RUN git clone https://github.com/dagster-io/dagster.git dagster \
    && cd dagster \
    && git checkout origin/docker4

WORKDIR /tmp/dagster

RUN pip install \
    -e python_modules/dagster \
    -e python_modules/libraries/dagster-postgres \
    -e python_modules/libraries/dagster-docker

ENV DAGSTER_HOME=/opt/dagster/dagster_home

RUN mkdir -p $DAGSTER_HOME

# Copy dagster instance YAML to $DAGSTER_HOME
COPY dagster.yaml $DAGSTER_HOME

# RUN chmod +w $DAGSTER_HOME

WORKDIR /opt/dagster/app

COPY repo.py /opt/dagster/app

EXPOSE 4000

# CMD allows the command to be overridden by run launchers and executors
# that want to access the code
CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-f", "repo.py"]