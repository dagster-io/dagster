####################################################################################################
#
# DAGSTER INTEGRATION IMAGE
#
# We use this Dockerfile to build an image for our Buildkite CI/CD pipeline.
# Python dependencies go here - system dependencies go in buildkite-integration-base.
#
####################################################################################################

ARG BASE_IMAGE
FROM "${BASE_IMAGE}" AS snapshot_builder

RUN apt-get update \
    && apt-get install -yqq \
        # Needed for matplotlib on 3.8.7
        pkg-config \
        libfreetype6 \
        libfreetype6-dev \
        libpng-dev

RUN git clone https://github.com/dagster-io/dagster.git \
    && cd dagster \
    && make install_dev_python_modules \
    && pip freeze --exclude-editable > /snapshot-reqs.txt


FROM "${BASE_IMAGE}"

COPY --from=snapshot_builder /snapshot-reqs.txt .

RUN apt-get update \
    && apt-get install -yqq \
        # Needed for matplotlib on 3.8.7
        pkg-config \
        libfreetype6 \
        libfreetype6-dev \
        libpng-dev \
    && apt-get remove -yqq \
    && apt-get autoremove -yqq --purge \
    && apt-get clean

RUN pip install -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt
