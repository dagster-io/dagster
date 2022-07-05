# Dagster Images

## Creating an image

For each image, create a new directory under `images/<YOUR IMAGE>`. Each image
folder should contain:

- **Dockerfile**
- **versions.yaml** - List of Python versions to build for and the Docker build
  arguments needed to build this image.
- **last_updated.yaml** - This file is machine-generated and will be updated
  automatically when you build the Docker image.

Then, `dagster-image build-all --name <YOUR IMAGE>` will build your image.

## Building and publishing images

The general workflow is to build images locally and then push them to AWS, from
which they are served to Buildkite etc. The command for building an image is:

    dagster-image build-all --name <IMAGE NAME> --dagster-version <DAGSTER VERSION> --platform=linux/amd64

This will build images for all Python versions specified in the corresponding
`versions.yaml`. Note that when building images for use in Buildkite (i.e.
`buildkite-test`, used for testing the tips of branches), you should specify
the version for the editable install of dagster, `0+dev`. Note also that the
`--platform=linux/amd64` might not always be necessary, but in the past it has
solved issues when building on an M1 mac.

You will not be able to publish images unless you are authenticated for ECR.
Ensure you are authenticated by running:

    aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 968703565975.dkr.ecr.us-west-2.amazonaws.com

Once you are authenticated, you can publish the newly built images with:

    dagster-image push-all --name <IMAGE NAME>

To see your published images on AWS, go to https://elementl.awsapps.com/start#/
and enter the "Management Console" for the "elementl" account (#968703565975).
Click through to "ECR" and you should see a list of "Private repositories".
Each repository corresponds to an image specification (e.g. `buildkite-test`)
and should contain multiple images (one for each version, as well as
past-published images).
