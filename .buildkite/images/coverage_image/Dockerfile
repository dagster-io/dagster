# This image is used to for the coverage step in the build process
FROM python:3.7.4-slim-stretch


RUN apt-get update \
    && apt-get -qq -y install lcov ruby-full git \
    && pip install coverage==4.5.4 coveralls coveralls-merge \
    && gem install coveralls-lcov \
    && apt-get remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/* /var/lib/apt/lists/*
