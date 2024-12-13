---
title: 'Serverless runtime environment'
sidebar_label: 'Runtime environment'
sidebar_position: 100
---

By default, Dagster+ Serverless will package your code as PEX files and deploys them on Docker images. Using PEX files significantly reduces the time to deploy since it does not require building a new Docker image and provisioning a new container for every code change. However you are able to customize the Serverless runtime environment in various ways:

- [Add dependencies](#add-dependencies)
- [Use a different Python version](#python-version)
- [Use a different base image](#base-image)
- [Include data files](#data-files)
- [Disable PEX deploys](#disable-pex)
- [Use private Python packages](#private-packages)

## Add dependencies \{#add-dependencies}

You can add dependencies by including the corresponding Python libraries in your Dagster project's `setup.py` file. These should follow [PEP 508](https://peps.python.org/pep-0508/).

<CodeExample
  filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/example_setup.py"
  language="Python"
  title="Example setup.py"
/>

You can also use a tarball to install a dependency, such as if `pip` is unable to resolve a package using `dependency_links`. For example, `soda` and `soda-snowflake` provide tarballs that you can include in the `install_requires` section:

```python
from setuptools import find_packages, setup

setup(
    name="quickstart_etl",
    packages=find_packages(exclude=["quickstart_etl_tests"]),
    install_requires=[
        "dagster",
        "boto3",
        "pandas",
        "matplotlib",
        'soda @ https://pypi.cloud.soda.io/packages/soda-1.6.2.tar.gz',
        'soda-snowflake @ https://pypi.cloud.soda.io/packages/soda_snowflake-1.6.2.tar.gz'
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
```

To add a package from a private GitHub repository, see: [Use private Python packages](#private-packages)

## Use a different Python version \{#python-version}

The default Python version for Dagster+ Serverless is Python 3.9. Python versions 3.10 through 3.12 are also supported. You can specify the Python version you want to use in your GitHub or GitLab workflow, or by using the `dagster-cloud` CLI.

<Tabs groupId="method">
<TabItem value="GitHub" label="GitHub">
In your `.github/workflows/deploy.yml` file, update the `PYTHON_VERSION` environment variable with your desired Python version:
<CodeExample filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/github_python_version.yaml" language="yaml" title="Updating the Python version in deploy.yml" />

</TabItem>
<TabItem value="GitLab" label="GitLab">
1. Open your `.gitlab-ci.yml` file. If your `.gitlab-ci.yml` contains an `include` with a link to a Dagster provided CI/CD template:
    <CodeExample filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/gitlab_template.yaml" language="yaml" />

    Follow the link and replace the contents of your `.gitlab-ci.yml` with the YAML document at the link address. Otherwise, continue to the next step.

3. Update the `PYTHON_VERSION` environment variable with your desired Python version

<CodeExample
  filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/gitlab_python_version.yaml"
  language="yaml"
  title="Updating the Python version in .gitlab-ci.yml"
/>

</TabItem>
<TabItem value="CLI" label="CLI">
You can specify the Python version when you deploy your code with the `dagster-cloud serverless deploy-python-executable` command:
```bash
dagster-cloud serverless deploy-python-executable --python-version=3.11 --location-name=my_location
```
</TabItem>
</Tabs>

## Use a different base image \{#base-image}

Dagster+ runs your code on a Docker image that we build as follows:

- The standard Python "slim" Docker image, such as python:3.8-slim is used as the base
- The dagster-cloud[serverless] module installed in the image

You can [add dependencies](#add-dependencies) in your `setup.py` file, but when that is not possible you can build and upload a custom base image that will be used to run your Python code:

:::note
Setting a custom base image isn't supported for GitLab CI/CD workflows out of the box, but you can write a custom GitLab CI/CD yaml file that implements the manual steps noted.
:::

1.  Include `dagster-cloud[serverless]` as a dependency in your Docker image by adding the following line to your `Dockerfile`:
    ```
    RUN pip install "dagster-cloud[serverless]"
    ```
2.  Build your Docker image, using your usual Docker toolchain.
3.  Upload your Docker image to Dagster+ using the `upload-base-image` command. This command will print out the tag used in Dagster+ to identify your image:

    ```bash
    $ dagster-cloud serverless upload-base-image local-image:tag

    ...
    To use the uploaded image run: dagster-cloud serverless deploy-python-executable ... --base-image-tag=sha256_518ad2f92b078c63c60e89f0310f13f19d3a1c7ea9e1976d67d59fcb7040d0d6
    ```

4.  Specify this base image tag in you GitHub workflow, or using the `dagster-cloud` CLI:

        <Tabs groupId="method">

    <TabItem value="GitHub" label="GitHub">
    In your `.github/workflows/deploy.yml` file, add the `SERVERLESS_BASE_IMAGE_TAG` environment variable and set it to the tag printed out in the previous step:
    <CodeExample filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/github_base_image.yaml" language="yaml" title="Setting a custom base image in deploy.yml" />

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

<CodeExample
  filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/data_files_setup.py"
  language="Python"
  title="Loading data files in setup.py"
/>

## Disable PEX deploys \{#disable-pex}

You have the option to disable PEX-based deploys and deploy using a Docker image instead of PEX. You can disable PEX in your GitHub or GitLab workflow, or by using the `dagster-cloud` CLI.

<Tabs groupId="method">
  <TabItem value="GitHub" label="GitHub">
  In your `.github/workflows/deploy.yml` file, update the `ENABLE_FAST_DEPLOYS` environment variable to `false`:
  <CodeExample filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/github_disable_pex.yaml" language="yaml" title="Disable PEX deploys in deploy.yml" />

  </TabItem>
  <TabItem value="GitLab" label="GitLab">
  1. Open your `.gitlab-ci.yml` file. If your `.gitlab-ci.yml` contains an `include` with a link to a Dagster provided CI/CD template:
      <CodeExample filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/gitlab_template.yaml" language="yaml" />

      Follow the link and replace the contents of your `.gitlab-ci.yml` with the YAML document at the link address. Otherwise, continue to the next step.

3. Update the `DISABLE_FAST_DEPLOYS` variable to `true`

<CodeExample
    filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/gitlab_disable_pex.yaml"
    language="yaml"
    title="Disable PEX deploys in .gitlab-ci.yml"
  />

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

1.  Build you base image
2.  Specify this base image tag in your GitHub workflow, or using the `dagster-cloud` CLI:

    <Tabs groupId="method">

      <TabItem value="GitHub" label="GitHub">
          In your `.github/workflows/deploy.yml` file, add the `SERVERLESS_BASE_IMAGE_TAG` environment variable and set it to the tag printed out in the previous step:
          <CodeExample filePath="dagster-plus/deployment/deployment-types/serverless/runtime-environment/github_no_pex_custom_base_image.yaml" language="yaml" title="Setting a custom base image in `deploy.yml`" />
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

## Use private Python packages \{#private-packages}

If you use PEX deploys in your workflow (`ENABLE_FAST_DEPLOYS: 'true'`), the following steps can install a package from a private GitHub repository, e.g. `my-org/private-repo`, as a dependency:

1.  In your `deploy.yml` file, add the following to the top of `steps:` section in the `dagster-cloud-default-deploy` job.

    ```yaml
    - name: Checkout internal repository
      uses: actions/checkout@v3
      with:
        token: ${{ secrets.GH_PAT }}
        repository: my-org/private-repo
        path: deps/private-repo
        ref: some-branch # optional to check out a specific branch

    - name: Build a wheel
      # adjust the `cd` command to cd into the directory with setup.py
      run: >
        cd deps/private-repo &&
        python setup.py bdist_wheel &&
        mkdir -p $GITHUB_WORKSPACE/deps &&
        cp dist/*whl $GITHUB_WORKSPACE/deps

    # If you have multiple private packages, the above two steps should be repeated for each but the following step is only
    # needed once
    - name: Configure dependency resolution to use the wheel built above
      run: >
        echo "[global]" > $GITHUB_WORKSPACE/deps/pip.conf &&
        echo "find-links = " >> $GITHUB_WORKSPACE/deps/pip.conf &&
        echo "    file://$GITHUB_WORKSPACE/deps/" >> $GITHUB_WORKSPACE/deps/pip.conf &&
        echo "PIP_CONFIG_FILE=$GITHUB_WORKSPACE/deps/pip.conf" > $GITHUB_ENV
    ```

2.  Create a GitHub personal access token and set it as the `GH_PAT` secret for your Actions.
3.  In your Dagster project's `setup.py` file, add your package name to the `install_requires` section:
    ```python
        install_requires=[
          "dagster",
          "dagster-cloud",
          "private-package",   # add this line - must match your private Python package name
    ```

Once the `deploy.yml` is updated and changes pushed to your repo, then any subsequent code deploy should checkout your private repository, build the package and install it as a dependency in your Dagster+ project. Repeat the above steps for your `branch_deployments.yml` if needed.
