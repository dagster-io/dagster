---
title: "Serverless runtime environment"
displayed_sidebar: "dagsterPlus"
sidebar_label: "Runtime environment"
sidebar_position: 30
---

With a Dagster+ Serverless deployment, you can customize the runtime environment where your code executes. You may want to:
- Use a different Python version.
- Install additional dependencies.
- Use a different base image.
- Include data files.

Dagster uses [PEX](https://docs.pex-tool.org/) to package your code and deploy them on Docker images. You also have the option to disable PEX-based deploys and deploy using a Docker image instead of PEX.

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A prerequisite, ex: "Familiarity with [Asset definitions](/concepts/assets)"
- Another prerequisite, ex: "To install this library"
- One more

</details>

## Use a different Python version
The default Python version for Dagster+ Serverless is Python 3.8. Python versions 3.9 through 3.12 are also supported. You can specify the Python version you want to use in your GitHub or GitLab workflow, or by using the `dagster-cloud` CLI.

<Tabs>
<TabItem value="GitHub" label="GitHub">
In your `.github/workflows/deploy.yml` file, update the `python_version` parameter for the `build_deploy_python_executable` job:
<CodeExample filePath="dagster-plus/deployment/serverless/runtime-environment/github_python_version.yaml" language="yaml" title="Updating the Python version in `deploy.yml`" />

</TabItem>
<TabItem value="GitLab" label="GitLab">
NEED TO FIGURE OUT IF WE CAN DO THIS ONE
</TabItem>
<TabItem value="CLI" label="CLI">
You can specify the Python version when you deploy your code with the `dagster-cloud serverless deploy-python-executable` command:
```bash
dagster-cloud serverless deploy-python-executable --python-version=3.11 --location-name=my_location
```
</TabItem>
</Tabs>

## Install additional dependencies

## Use a different base image

## Include data files

## Disable PEX deploys
