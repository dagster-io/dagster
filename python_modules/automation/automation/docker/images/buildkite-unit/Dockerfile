####################################################################################################
#
# DAGSTER UNIT IMAGE
#
# We use this Dockerfile to build an unit test image for our Buildkite CI/CD pipeline.
#
####################################################################################################
ARG BASE_IMAGE
FROM "${BASE_IMAGE}" AS apt_base

RUN apt-get update -yqq \
    && apt-get install -yqq \
        build-essential \
        cron \
        g++ \
        gcc \
        git \
        make

RUN git clone https://github.com/dagster-io/dagster.git

WORKDIR dagster

FROM apt_base AS snapshot_builder

# Build a requirements file with all non-Dagster packages
RUN make install_dev_python_modules \
    && pip freeze --exclude-editable > /snapshot-reqs.txt

FROM apt_base

COPY --from=snapshot_builder /snapshot-reqs.txt .

RUN pip install -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt
