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

# Build a requirements file with all non-Dagster packages
RUN git clone https://github.com/dagster-io/dagster.git \
    && cd dagster \
    && make install_dev_python_modules \
    && pip freeze --exclude-editable > /snapshot-reqs.txt


FROM "${BASE_IMAGE}"

COPY --from=snapshot_builder /snapshot-reqs.txt .

# Preinstall non-Dagster packages in image so that the virtual environment
# builds faster in Buildkite.
RUN pip install -r /snapshot-reqs.txt \
    && rm /snapshot-reqs.txt
