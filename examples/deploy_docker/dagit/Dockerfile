FROM python:3.7-slim

WORKDIR /tmp

# Install git
RUN apt-get update && apt-get install -yqq git curl

RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - \
    # Add yarn repo
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list \
    && apt-get update -yqq \
    && apt-get upgrade -yqq

RUN apt-get install -yqq yarn

RUN git clone https://github.com/dagster-io/dagster.git dagster \
    && cd dagster \
    && git checkout origin/docker3

WORKDIR /tmp/dagster/

RUN pip install \
    -e python_modules/dagster \
    -e python_modules/dagster-graphql \
    -e python_modules/dagit \
    -e python_modules/libraries/dagster-postgres \
    -e python_modules/libraries/dagster-docker


WORKDIR /tmp/dagster/js_modules/dagit/


RUN yarn install
RUN yarn build-for-python

RUN mkdir -p /opt/dagster/dagster_home

ENV DAGSTER_HOME=/opt/dagster/dagster_home/

RUN mkdir -p $DAGSTER_HOME

# Copy dagster instance YAML to $DAGSTER_HOME
COPY dagster.yaml workspace.yaml $DAGSTER_HOME

EXPOSE 3000

WORKDIR /opt/dagster/dagster_home/

ENTRYPOINT ["dagit", "-h", "0.0.0.0", "-p", "3000", "-w", "workspace.yaml"]