---
title: "Serverless runtime environment"
displayed_sidebar: "dagsterPlus"
sidebar_label: "Runtime environment"
sidebar_position: 30
---

With a Dagster+ Serverless deployment, you can customize the runtime environment where your code executes. You may want to:
- [Use a different Python version](#python-version).
- [Use a different base image](#base-image).
- [Include data files](#data-files).

Dagster uses [PEX](https://docs.pex-tool.org/) to package your code and deploy them on Docker images. You also have the option to [disable PEX-based deploys](#disable-pex) and deploy using a Docker image instead of PEX.


## Use a different Python version \{#python-version}
The default Python version for Dagster+ Serverless is Python 3.8. Python versions 3.9 through 3.12 are also supported. You can specify the Python version you want to use in your GitHub or GitLab workflow, or by using the `dagster-cloud` CLI.

<Tabs groupId="method">
<TabItem value="GitHub" label="GitHub">
In your `.github/workflows/deploy.yml` file, update the `PYTHON_VERSION` environment variable with your desired Python version:
<CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/github_python_version.yaml" language="yaml" title="Updating the Python version in deploy.yml" />

</TabItem>
<TabItem value="GitLab" label="GitLab">
1. Open your `.gitlab-ci.yml` file. If your `.gitlab-ci.yml` contains an `include` with a link to a Dagster provided CI/CD template:
    <CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/gitlab_template.yaml" language="yaml" />

    Follow the link and replace the contents of your `.gitlab-ci.yml` with the YAML document at the link address. Otherwise, continue to the next step.

3. Update the `PYTHON_VERSION` environment variable with your desired Python version

    <CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/gitlab_python_version.yaml" language="yaml" title="Updating the Python version in .gitlab-ci.yml" />

</TabItem>
<TabItem value="CLI" label="CLI">
You can specify the Python version when you deploy your code with the `dagster-cloud serverless deploy-python-executable` command:
```bash
dagster-cloud serverless deploy-python-executable --python-version=3.11 --location-name=my_location
```
</TabItem>
</Tabs>


## Use a different base image \{#base-image}
When possible, you should add dependencies by including the corresponding Python libraries in your Dagster project's `setup.py` file:
<CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/example_setup.py" language="Python" title="Example setup.py" />

When adding dependencies with the `setup.py` file isn't possible, you can build a custom base image:

:::note
Setting a custom base image isn't supported for GitLab CI/CD workflows out of the box, but you can write a custom GitLab CI/CD yaml file that implements the manual steps noted.
:::

1. Include `dagster-cloud[serverless]` as a dependency in your Docker image by adding the following line to your `Dockerfile`:
    ```
    RUN pip install "dagster-cloud[serverless]"
    ```
2. Build your Docker image, using your usual Docker toolchain.
3. Upload your Docker image to Dagster+ using the `upload-base-image` command. This command will print out the tag used in Dagster+ to identify your image:
    ```bash
    $ dagster-cloud serverless upload-base-image local-image:tag

    ...
    To use the uploaded image run: dagster-cloud serverless deploy-python-executable ... --base-image-tag=sha256_518ad2f92b078c63c60e89f0310f13f19d3a1c7ea9e1976d67d59fcb7040d0d6
    ```

4. Specify this base image tag in you GitHub workflow, or using the `dagster-cloud` CLI:
    <Tabs groupId="method">
    <TabItem value="GitHub" label="GitHub">
    In your `.github/workflows/deploy.yml` file, add the `SERVERLESS_BASE_IMAGE_TAG` environment variable and set it to the tag printed out in the previous step:
    <CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/github_base_image.yaml" language="yaml" title="Setting a custom base image in deploy.yml" />

    </TabItem>
    <TabItem value="CLI" label="CLI">
    You can specify the base image when you deploy your code with the `dagster-cloud serverless deploy-python-executable` command:
    ```bash
    dagster-cloud serverless deploy-python-executable \
    --base-image-tag=sha256_518ad2f92b078c63c60e89f0310f13f19d3a1c7ea9e1976d67d59fcb7040d0d6 \
    --location-name=my_location
    ```
    </TabItem>
    </Tabs>

## Include data files \{#data-files}
To add data files to your deployment, use the [Data Files Support](https://setuptools.pypa.io/en/latest/userguide/datafiles.html) built into Python's `setup.py`. This requires adding a `package_data` or `include_package_data` keyword in the call to `setup()` in `setup.py`. For example, given this directory structure:

```
- setup.py
- quickstart_etl/
  - __init__.py
  - definitions.py
  - data/
    - file1.txt
    - file2.csv
```

If you want to include the data folder, modify your `setup.py` to add the `package_data` line:
<CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/data_files_setup.py" language="Python" title="Loading data files in setup.py" />

## Disable PEX deploys \{#disable-pex}

Prior to using PEX files, Dagster+ deployed code using Docker images. This feature is still available.

You can disable PEX in your GitHub or GitLab workflow, or by using the `dagster-cloud` CLI.

<Tabs groupId="method">
<TabItem value="GitHub" label="GitHub">
In your `.github/workflows/deploy.yml` file, update the `ENABLE_FAST_DEPLOYS` environment variable to `false`:
<CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/github_disable_pex.yaml" language="yaml" title="Disable PEX deploys in deploy.yml" />

</TabItem>
<TabItem value="GitLab" label="GitLab">
1. Open your `.gitlab-ci.yml` file. If your `.gitlab-ci.yml` contains an `include` with a link to a Dagster provided CI/CD template:
    <CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/gitlab_template.yaml" language="yaml" />

    Follow the link and replace the contents of your `.gitlab-ci.yml` with the YAML document at the link address. Otherwise, continue to the next step.

3. Update the `DISABLE_FAST_DEPLOYS` variable to `true`

    <CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/gitlab_disable_pex.yaml" language="yaml" title="Disable PEX deploys in .gitlab-ci.yml" />

</TabItem>
<TabItem value="CLI" label="CLI">
You can deploy using a Docker image instead of PEX by using the `dagster-cloud serverless deploy` command instead of the `dagster-cloud-serverless deploy-python-executable` command:

```bash
dagster-cloud serverless deploy --location-name=my_location
```
</TabItem>
</Tabs>


You can customize the Docker image using lifecycle hooks or by customizing the base image:

<Tabs groupId="method">
<TabItem value="lifecycle-hooks" label="Lifecycle hooks">
This method is the easiest to set up, and doesn't require setting up any additional infrastructure.

In the root of your repo, you can provide two optional shell scripts: `dagster_cloud_pre_install.sh` and `dagster_cloud_post_install.sh`. These will run before and after Python dependencies are installed. They're useful for installing any non-Python dependencies or otherwise configuring your environment.

</TabItem>
<TabItem value="base-image" label="Base image">
This method is the most flexible, but requires setting up a pipeline outside of Dagster to build a custom base image.

:::note
Setting a custom base image isn't supported for GitLab CI/CD workflows out of the box, but you can write a custom GitLab CI/CD yaml file that implements the manual steps noted.
:::

1. Build you base image
2. Specify this base image tag in your GitHub workflow, or using the `dagster-cloud` CLI:
    <Tabs groupId="method">
    <TabItem value="GitHub" label="GitHub">
    In your `.github/workflows/deploy.yml` file, add the `SERVERLESS_BASE_IMAGE_TAG` environment variable and set it to the tag printed out in the previous step:
    <CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/github_no_pex_custom_base_image.yaml" language="yaml" title="Setting a custom base image in `deploy.yml`" />

    </TabItem>
    <TabItem value="CLI" label="CLI">
    You can specify the base image when you deploy your code with the `dagster-cloud serverless deploy` command:
    ```bash
    dagster-cloud serverless deploy --base-image=my_base_image:latest --location-name=my_location
    ```
    </TabItem>
    </Tabs>
</TabItem>

</Tabs>
