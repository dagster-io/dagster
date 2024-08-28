---
title: "Code locations"
displayed_sidebar: "dagsterPlus"
---

# Code locations

Separate code locations allow you to deploy different projects that still roll up into a single Dagster+ deployment with one global lineage graph. To add your first code location, follow the [getting started](/dagster-plus/getting-started) guide.

This guide will cover three options for adding a new code location:
- Adding a code location manually
- Adding a code location in a new Git repository
- Adding a new code location to an existing Git monorepo

<details>
<summary>Prerequisites</summary>

1. You should have a Dagster project, we recommend setting this project up as a Python module following our [recommended project structure](/tutorial/create-new-project).

2. You should know whether or not you are using Dagster Plus Serverless or Dagster Plus Hybrid. Your administrator will know that, or you can find the agent type by navigating to your Dagster+ organization, clicking on the "Deployment" page, and selecting the "Agent" tab. Dagster+ Serverless organizations will have a label "Managed by Dagster+".

</details>

Adding a code location follows two steps:
- For Dagster+ Hybrid, ensuring the Dagster code is in a place accessible by your agent, usually by building a Docker image with your code that is pushed to a registry. For Dagster+ Serverless you can skip this step.
- Notifying Dagster+ of the new or updated code location. This will be done by using the Dagster+ Python client.

Often these two steps are handled by CI/CD connected to your Git repository.


## Add a new code location manually

Start by installing the `dagster-cloud` Python client:

```
pip install dagster-cloud
```

Next you will want need to authenticate this Python client:

1. In the Dagster+ UI, click on your user icon in the upper right corner.
2. Click **Organization settings**, then the **Tokens** tab.
3. Click the **Create user token** button. 
4. Copy the token.

2. Set the following environment variables:

   ```bash
   export  DAGSTER_CLOUD_ORGANIZATION="organization-name" # if your URL is https://acme.dagster.plus your organization name is "acme"
   export  DAGSTER_CLOUD_API_TOKEN="your-token"
   ```

3. Add the code location. The following example assumes you are running the command from the top-level working directory of your Dagster project with a project named "quickstart" structured as a Python module named "quickstart".

```bash
$pwd
/projects/quickstart
$tree
/quickstart
    setup.py
    pyproject.toml
    /quickstart
        __init__.py
        /assets
        /resources
```

If you are using Dagster+ Serverless, run the following command to add a code location:

```bash
dagster-cloud serverless deploy-python-executable --deployment prod --location-name quickstart --module-name quickstart
```

Use `dagster-cloud serverless deploy-python-executable --help` to see all available options. Running the command multiple times with the same location name will *update* the code location. Running the command with a new location name will *add* a code location.

If you are using Dagster+ Hybrid, make sure you have deployed the code appropriately by building a Docker image and pushing it to a Git repository. Then run:

```bash
dagster-cloud deployment add-location --deployment prod --location-name quickstart --module-name quickstart --image 764506304434.dkr.ecr.us-west-2.amazonaws.com/hooli-data-science-prod:latest
```

## Adding a code location in a new Git repository

Adding a code location to a Git repository follows the same steps as adding a code location manually, but automates those steps by running them through CICD. The best way to get started is to structure your repository following one of the Dagster+ template repositories:

- [GitHub repository with Dagster+ Serverless](https://github.com/dagster-io/dagster-cloud-serverless-quickstart/)
- [GitHub repository with Dagster+ Hybrid](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/)
- [Gitlab CICD for Dagster+ Serverless](https://github.com/dagster-io/dagster-cloud-action/blob/main/gitlab/serverless-ci.yml)
- [Gitlab CICD for Dagster+ Hybrid](https://github.com/dagster-io/dagster-cloud-action/blob/main/gitlab/hybrid-ci.yml)


Overall, the Git repository should contain:

1. Your Dagster code, structured as a Python module. The repository might look like this:

```bash
README.md
dagster_cloud.yaml
Dockerfile
/.github
    /workflows
        dagster-cloud-deploy.yml
setup.py
pyproject.toml
/quickstart
    __init__.py
    definitions.py
    /assets
        ...
    /resources
        ...
```

2. A `dagster_cloud.yaml` file with the settings for your code location. Here is an example:

```yaml
locations:
  - location_name: quickstart
    code_source:
      package_name: quickstart
```

3. A CI/CD workflow file that contains the steps for adding your code location. Here is an example workflow file for a Dagster+ Hybrid organization:

```yaml
variables:
  DAGSTER_CLOUD_ORGANIZATION: <organinization-name>
  DAGSTER_PROJECT_DIR: .
  IMAGE_REGISTRY: <account-id>.dkr.ecr.us-west-2.amazonaws.com/<image-name>
  IMAGE_TAG: $CI_COMMIT_SHORT_SHA-$CI_PIPELINE_ID

stages:
  - build
  - deploy

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    # # For Gitlab Container Registry
    # - echo $CI_JOB_TOKEN | docker login --username $CI_REGISTRY_USER --password-stdin $REGISTRY_URL
    # # For DockerHub
    # - echo $DOCKERHUB_TOKEN | docker login --username $DOCKERHUB_USERNAME --password-stdin $REGISTRY_URL
    # # For AWS Elastic Container Registry (ECR)
    # - apk add --no-cache curl jq python3 py3-pip
    # - pip install awscli
    # - echo $AWS_ECR_PASSWORD | docker login --username AWS --password-stdin $IMAGE_REGISTRY
    # # For Google Container Registry (GCR)
    # - echo $GCR_JSON_KEY | docker login --username _json_key --password-stdin $REGISTRY_URL
  script:
    - docker build . -t $IMAGE_REGISTRY:$IMAGE_TAG
    - docker push $IMAGE_REGISTRY:$IMAGE_TAG

deploy:
  stage: deploy
  dependencies:
    - build
  image: ghcr.io/dagster-io/dagster-cloud-action:0.1.43
  script:
    - dagster-cloud deployment add-location --deployment prod --image
    $IMAGE_REGISTRY:$IMAGE_TAG --location-name quickstart --package-name quickstart
```

## Adding a new code location to a Git monorepo

Many organizations use a Git monorepo to contain multiple Dagster projects. Here is an example of DagsterLab's own [internal data engineering Git repository](https://github.com/dagster-io/dagster-open-platform).

To add a new code location to a monorepo, create a new directory that contains:
- Your Dagster project
- For Dagster+ Hybrid, you will typically add a Dockerfile:

```
FROM python:3.11-slim
# Add any steps to install project system dependencies like java

WORKDIR /opt/dagster/app

COPY . /opt/dagster/app

# Add steps to install the Python dependencies for your Dagster project
# into the default Python on PATH
# For example, this project uses setup.py and we install all dependencies into the Docker container
# using `pip`.

RUN pip install -e .
```

The final repository structure might look like this:

```
README.md
dagster_cloud.yaml
/.github
    ...
/shared
    setup.py
    pyproject.toml
    /shared
        __init__.py
        utilities.py
/core
    setup.py
    pyproject.toml
    Dockerfile
    /core
        definitions.py
        __init__.py
        /assets
/new-code-location
    setup.py
    pyproject.toml
    Dockerfile
    /new-code-location
        definitions.py
        __init__.py
        /assets
```

Then you will update the `dagster_cloud.yaml` file in the root of the Git repository:

```yaml
locations:
  - location_name: core
    code_source:
      package_name: core
    build:
      directory: ./core
      registry:  your-registry/image # eg 764506304434.dkr.ecr.us-west-2.amazonaws.com/core
  - location_name: new
    code_source:
      package_name: new
    build:
      directory: ./new
      registry: your-registry/image # eg 764506304434.dkr.ecr.us-west-2.amazonaws.com/new
```

The monorepo should have CICD configured to deploy your changes and add or update your new code location.

## Next steps

- After adding a code location, you may want to setup access controls
- You may want to add additional configuration to your code location. This configuration will vary by agent type, but see examples for [setting default resource limits for Kubernetes](/dagster-plus/deployment/agents/kubernetes) or [changing the IAM role for ECS](/dagster-plus/deployment/agents/amazon-ecs).