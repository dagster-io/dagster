# Dagster Images

## Creating an image

For each image, create a new directory under `images/<YOUR IMAGE>`. Each image folder should
contain:

- **Dockerfile**
- **versions.yaml** - List of Python versions to build for and the Docker build arguments needed to
  build this image.
- **last_updated.yaml** - This file is machine-generated and will be updated automatically when you
  build the Docker image.

Then, `dagster-image build-all --name <YOUR IMAGE>` will build your image.

## Integration Images

Building our integration images is a two-step process. One is the creation of a fixed set of
requirements that are checked in at `images/buildkite-integration`. This is typically done on your
development machine. You then put up a diff with these altered snapshot files and then instigate a
build to build a fresh snapshot image. See detailed instructions below.

The snapshot requirement files are locked at a given git hash (H) and a given time (T) when the
snapshots were built. The git hash H locks set set of dependencies required. The time T sets the
versions that were downloaded from the public pypi at a particular time. The hash H is in the file
`images/buildkite-integration-snapshot-builder/Dockerfile`. The time T is in `.buildkite/defines.py`
in the `INTEGRATION_IMAGE_VERSION` variable.

### Publishing new integration images

1. Update the git hash in `images/buildkite-integration-snapshot-builder/Dockerfile`.
2. Run: `dagster-image build-all --name buildkite-integration-snapshot-builder`
3. Run: `dagster-image snapshot -t integration`
4. Then run `dagster-image build-all --name buildkite-integration`
5. Then run `dagster-image push-all --name buildkite-integration`
6. Update `INTEGRATION_IMAGE_VERSION` and put up a diff with these planned changes.

### Publishing new unit images

Similarly we have a similar system for the unit test images. These are more
modest and require less build times so we have not pushed the process
to a pipeline in buildkite.

1. Update the git hash in `images/buildkite-unit-snapshot-builder/Dockerfile`
2. Run, with the appropriate Dagster version,
   `dagster-image build-all --name buildkite-unit-snapshot-builder --dagster-version 0.9.18`
3. Run: `dagster-image snapshot -t unit`
4. Then run, with the appropriate Dagster version,
   `dagster-image build-all --name buildkite-unit --dagster-version 0.9.18`
5. Then run `dagster-image push-all --name buildkite-unit`
6. Next you have to update the Dockerfile in `dagster-test` manually with the value in
   `UNIT_IMAGE_VERSION` in the `FROM` directive.
7. Update `UNIT_IMAGE_VERSION` and put up a diff with these planned changes.
