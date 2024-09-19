FROM mcr.microsoft.com/devcontainers/python:3.11
ENV PYTHONUNBUFFERED 1

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && \
    apt-get install -y gdal-bin libgdal-dev g++
COPY setup.py .
RUN pip3 --disable-pip-version-check --no-cache-dir install -e .[dev] \
    && rm -rf /tmp/pip-tmp
COPY . .