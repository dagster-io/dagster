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

## Integration & unit images

For all of the steps below, you should first ensure you are authed for ECR, e.g. by running
`aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 968703565975.dkr.ecr.us-west-2.amazonaws.com`.

If you are on an M1 mac, you may need to specify `--platform=linux/amd64` when
building images.

When building images for use in Buildkite (i.e. imagse for testing the tips of
branches), specify the version for the editable install of dagster, `0+dev`.

### Publishing new integration images

1. Run with the appropriate Dagster version:
   `dagster-image build-all --name buildkite-integration --dagster-version 0.9.20`
2. Then run `dagster-image push-all --name buildkite-integration`

### Publishing new unit images

1. Run with the appropriate Dagster version:
   `dagster-image build-all --name buildkite-unit --dagster-version 0.9.20`
2. Run `dagster-image push-all --name buildkite-unit`
