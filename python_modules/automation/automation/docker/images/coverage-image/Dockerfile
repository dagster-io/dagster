# This image is used to for the coverage step in the build process
ARG BASE_IMAGE
FROM "${BASE_IMAGE}"


RUN apt-get update \
    && apt-get -qq -y install lcov ruby-full git \
    && pip install coverage==5.3 coveralls coveralls-merge \
    && gem install coveralls-lcov \
    && apt-get remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*
