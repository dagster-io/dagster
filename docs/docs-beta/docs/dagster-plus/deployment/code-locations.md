---
title: "Code locations"
displayed_sidebar: "dagsterPlus"
---

# Code locations

Separate code locations allow you to deploy different projects that still roll up into a single Dagster+ deployment with one global lineage graph.

This guide will cover three options for adding a new code location:
- Adding a code location manually
- Adding a code location in a new Git repository
- Adding a new code location to an existing Git monorepo

<details>
<summary>Prerequisites</summary>

1. An existing Dagster project. Refer to the [recommended project structure](/tutorial/create-new-project) and [code requirements](/dagster-plus/deployment/code-requirements) pages for more information.

2. Editor, Admin, or Organization Admin permissions in Dagster+.

3. To know your Dagster+ deployment type. An administrator can help find this information, or you can locate it by clicking *Deployment > Agents tab* in the Dagster UI. Dagster+ Serverless organizations will have a *Managed by Dagster+* label next to the agent.

</details>

Adding a code location follows two steps:
- For Dagster+ Hybrid, ensuring the Dagster code is in a place accessible by your agent, usually by building a Docker image with your code that's pushed to a registry. For Dagster+ Serverless you can skip this step.
- Notifying Dagster+ of the new or updated code location. This will be done by using the Dagster+ Python client.

Often these two steps are handled by CI/CD connected to your Git repository.


## Add a new code location manually

Start by installing the `dagster-cloud` Python client:

```
pip install dagster-cloud
```

Next you will want need to authenticate this Python client:

1. In the Dagster+ UI, click the user icon in the upper right corner.
2. Click **Organization settings**, then the **Tokens** tab.
3. Click the **Create user token** button.
4. Copy the token.
5. Set the following environment variables:

   ```bash
   export  DAGSTER_CLOUD_ORGANIZATION="organization-name" # if your URL is https://acme.dagster.plus your organization name is "acme"
   export  DAGSTER_CLOUD_API_TOKEN="your-token"
   ```

Now add the code location. The following example assumes you are running the command from the top-level working directory of your Dagster project with a project named "quickstart" structured as a Python module named "quickstart".

```bash
/quickstart
    setup.py
    pyproject.toml
    /quickstart
        __init__.py
        /assets
        /resources
```

The commands below take two main arguments:
- `module_name` is determined by your code structure
- `location_name` is the unique label for this code location used in Dagster+

<Tabs>
<TabItem value="serverless" label="Dagster+ Serverless">

If you are using Dagster+ Serverless, run the following command to add a code location:

```bash
dagster-cloud serverless deploy-python-executable --deployment prod --location-name quickstart --module-name quickstart
```

Running the command multiple times with the same location name will *update* the code location. Running the command with a new location name will *add* a code location.
</TabItem>
<TabItem value="hybrid" label="Dagster+ Hybrid">

If you are using Dagster+ Hybrid, make sure you have deployed the code appropriately by [building a Docker image and pushing it to an image registry](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart). Then run this command, using the image URI which is available from your registry:

```bash
dagster-cloud deployment add-location --deployment prod --location-name quickstart --module-name quickstart --image 764506304434.dkr.ecr.us-west-2.amazonaws.com/hooli-data-science-prod:latest
```
</TabItem>
</Tabs>

After running the command you can verify the code location was deployed by navigating to the *Deployments* tab on Dagster+.

## Adding a code location in a new Git repository

Adding a code location to a Git repository follows the same steps as adding a code location manually, but automates those steps by running them through CI/CD.

To get started, review the appropriate example repository and then create your Git repository with the same structure.

- [GitHub repository with Dagster+ Serverless](https://github.com/dagster-io/dagster-cloud-serverless-quickstart/)
- [GitHub repository with Dagster+ Hybrid](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/)
- [GitLab CI/CD for Dagster+ Serverless](https://github.com/dagster-io/dagster-cloud-action/blob/main/gitlab/serverless-ci.yml)
- [GitLab CI/CD for Dagster+ Hybrid](https://github.com/dagster-io/dagster-cloud-action/blob/main/gitlab/hybrid-ci.yml)


Overall, the Git repository should contain:

1. Your Dagster code, structured as a Python module. For Dagter+ Hybrid you may need a [Dockerfile](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/Dockerfile) as well. The repository might look like this:

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

2. A [`dagster_cloud.yaml` file](/todo) with the settings for your code location. Here is an example:

    ```yaml title="dagster_cloud.yaml
    locations:
    - location_name: quickstart
        code_source:
        package_name: quickstart
    ```

3. A CI/CD workflow file that contains the steps for adding your code location. These are the same steps outlined in the preceding section. Here is a minimal example workflow file for a Dagster+ Hybrid organization based on [this GitLab template](https://github.com/dagster-io/dagster-cloud-action/blob/main/gitlab/hybrid-ci.yml).

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

Once your Git repository has this structure, you will want to run your CI/CD process. The CI/CD process will add the code location to Dagster+ which can be verified by viewing the *Deployments* tab.

## Adding a new code location to a Git monorepo

Many organizations use a Git monorepo to contain multiple Dagster projects. Here is an example of DagsterLab's own [internal data engineering Git repository](https://github.com/dagster-io/dagster-open-platform).

To add a new code location to a monorepo, create a new directory that contains your Dagster project. The final repository structure might look like this:

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

Then update the `dagster_cloud.yaml` file in the root of the Git repository, adding a location section for your project including the location name, code source, and build directory. For Dagster+ Hybrid, include the registry. If you don't know the registry, consult your administrator or the team that set up CI/CD for the Git repository.

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

The monorepo should have CI/CD configured to deploy your changes and add or update your new code location. After adding your code and updating the `dagster_cloud.yaml` file, trigger the CI/CD process to add your code location to Dagster+. Navigate to the *Deployments* tab in Dagster+ to confirm your code location was added.

## Next steps

- After adding a code location, you may want to setup access controls
- You may want to add additional configuration to your code location. This configuration will vary by agent type, but see examples for [setting default resource limits for Kubernetes](/dagster-plus/deployment/hybrid/agents/kubernetes) or [changing the IAM role for ECS](/todo).
