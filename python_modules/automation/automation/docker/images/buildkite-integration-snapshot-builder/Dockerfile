ARG BASE_IMAGE
FROM "${BASE_IMAGE}"

# Last git commit in dagster that build the snapshot files
RUN git clone https://github.com/dagster-io/dagster.git dagster \
    && cd dagster \
    && git checkout 6cdb258f3e7b6c92d5b6cf530d47a08f6f7a0e8d

# for some reason this is only failing in the 3.8 image
# RUN cd dagster && git checkout "${SNAPSHOT_GIT_HASH}"

RUN cd dagster && make install_dev_python_modules_verbose
