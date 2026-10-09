# Dagster Images

- `dagster-celery-k8s` (Helm default): Host process image for Dagster Webserver, Daemon, and Celery workers. We use this
  as the default so that users can switch to Celery without hitting a dependency issue.
- `user-code-example` (Helm default): Example job code.
- `dagster-k8s`: `dagster-celery-k8s` without the Celery dependency.

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
the version for the editable install of dagster, `1!0+dev`. Note also that the
`--platform=linux/amd64` might not always be necessary, but in the past it has
solved issues when building on an M1 mac.

You will not be able to publish images unless you are authenticated for ECR.
Ensure you are authenticated by running:

    $ aws sso login
    $ aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 968703565975.dkr.ecr.us-west-2.amazonaws.com

Once you are authenticated, you can publish the newly built images with:

    dagster-image push-all --name <IMAGE NAME>

To see your published images on AWS, go to https://elementl.awsapps.com/start#/
and enter the "Management Console" for the "elementl" account (#968703565975).
Click through to "ECR" and you should see a list of "Private repositories".
Each repository corresponds to an image specification (e.g. `buildkite-test`)
and should contain multiple images (one for each version, as well as
past-published images).

## Publishing multi-platform images to Docker Hub

Use `build-and-push-dockerhub` to build and publish `dagster-k8s`,
`dagster-celery-k8s`, or `user-code-example` for both `linux/amd64` and
`linux/arm64`. It pushes both architectures under the same version tag, so
Docker selects the matching image on each host.

First, log in to Docker Hub and configure a Docker Buildx builder that supports
both platforms. For example:

```sh
docker login
docker buildx create --name dagster-multiarch --driver docker-container --use
docker buildx inspect --bootstrap
```

Check that both `linux/amd64` and `linux/arm64` are listed in the builder's
platforms. Linux builders need native ARM64 nodes or QEMU/binfmt support;
Docker Desktop includes emulation. The base image, including any `BASE_IMAGE`
registry mirror override, must also support both architectures.

```sh
dagster-image build-and-push-dockerhub \
  --name dagster-celery-k8s \
  --dagster-version "<dagster-version>"
```

Add `--set-latest` when the release should also update `latest`. To override
the default platforms, repeat `--platform`, for example `--platform linux/arm64`
for an ARM64-only build.

For multi-platform Docker Hub releases, this command replaces the separate
`build` and `push-dockerhub` steps. It does not load a local image or update
`last_updated.yaml`. The existing local build and ECR publishing commands are
unchanged; release automation must adopt the new command to publish both
architectures to Docker Hub.

Verify the published platforms with:

```sh
docker buildx imagetools inspect "dagster/dagster-celery-k8s:<dagster-version>"
```
