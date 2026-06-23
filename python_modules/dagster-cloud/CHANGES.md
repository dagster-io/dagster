# Dagster Cloud Changelog

> [!IMPORTANT]
> This changelog is deprecated. New releases will be documented in the main [Dagster Changelog](https://github.com/dagster-io/dagster/blob/master/CHANGES.md).

# 1.2.7

### New

- The ECS Agent now supports setting volumes and mount points

# 1.2.5

### New

- The Kubernetes agent will now include additional debug information when a new code location fails to start up after being deployed, instead of just showing a timeout error message.

# 1.2.4

### New

- Alerts without any tags are now more clearly indicated in the Dagster Cloud UI as affecting all jobs.

### Bugfixes

- Fixed an issue where loading assets with many partitions sometimes showed an error in the Dagster Cloud UI.
- The Dagster Cloud Agent is now more resilient to network errors when uploading responses to API requests.

# 1.2.3

### Bugfixes

- Removed a pinned package to fix a dependency incompatibility between `dagster-cloud` and `black`.
- Fixed a UI bug which prevented adding a code location through the GitHub integration multiple times.

# 1.2.2

### Bugfixes

- Fixed an issue where some SAML SSO apps that didn’t set the RelayState field failed to work with Dagster Cloud

# 1.2.1 Cloud

No changes (keeping pace with `dagster` package)

# 1.2.0

### New

- Added a new Users tab on the Cloud Settings page with a number of permissions improvements:
  - A way to see all the permissions for each user and deployment in a single place
  - A way to set permissions for all branch deployments (there's a separate "Branch deployments" column in the UI that can set its own permissions)
  - A new Launcher role that can launch and terminate runs and backfills, but can take no other writes (Only available on Enterprise plans)
  - Setting permissions per code location within a deployment (Only available on Enterprise plans)

  This new tab replaces the old Permissions tab. See [the docs](https://docs.dagster.io/master/dagster-cloud/account/managing-users) for more information.

- Added Gitlab integration for adding code locations to Serverless deployments

# 1.1.21

### New

- The ECS Agent now allows you to set the `runtimePlatform` for task definitions of the tasks that it creates, allowing you to create tasks using a Windows Docker image.
- Additional information about the code servers and run workers managed by an agent can be viewed in the agent statuses section.

### Bugfixes

- Fixed a GraphQL error that occurred when a freshness policy sensor ran with a time-partitioned asset
- Fixed a `dagster-cloud` GitHub workflow bug to gracefully handle the case when the commit author is not a GitHub user.

# 1.1.20

### New

- ECS Hybrid agents can now change the IAM roles used to spin up tasks for different code locations within the same deployment. See [the docs](https://docs.dagster.io/dagster-cloud/deployment/agents/amazon-ecs/configuration-reference#amazon-ecs-agent-configuration-reference) for an example of how to set the IAM roles for a particular code location in a `dagster_cloud.yaml` file.

### Breaking Changes

- The `dagster-cloud serverless build-python-executable` command now automatically falls back to using a docker environment to build the Python dependencies, if the current environment cannot build the dependencies. This may happen when some packages do not publish a compatible Linux wheel in PyPI. The `--build-in-linux-docker` flag has been removed and replaced with a `--build-method` flag. This can be be set to `docker-fallback` (default), `local` to use the local environment only, or `docker` to only use the docker environment and skip the local environment.

# 1.1.19

### New

- Alerts can now be configured to notify on code location load error. Just create a new alert policy from the UI, and the option will be available.

### Bugfixes

- Fixed an issue where Serverless code location updates sometimes timed out while using the ENABLE_FAST_DEPLOYS flag.
- Fixed an issue where copying permissions from a deployment with only organization admins when creating a new deployment would raise an error message.

# 1.1.18

### New

- Alerts can now be configured for Agent downtime on hybrid deployments. Check out the alerting documentation to learn more: https://docs.dagster.io/dagster-cloud/account/setting-up-alerts#setting-up-alerts-in-dagster-cloud.
- Users with Editor permissions can now edit deployment settings within the Dagster Cloud UI. Previously, they could only edit deployment settings using the dagster-cloud CLI.
- Serverless runs are now isolated by default. Isolated runs receive more memeory and compute, but take longer to start. https://docs.dagster.io/dagster-cloud/deployment/serverless#run-isolation

### Bugfixes

- Fixed a bug where schedule / sensor alerts would not fire upon re-enabling an alert policy.

# 1.1.15

### New

- Significant performance improvements for the asset reconciliation sensor when running on large asset graphs.
- [dagit] The Permissions and Alerts sections of Cloud Settings have been moved to the Deployment section of the app.

### Bugfixes

- Some issues in `dagster-cloud serverless deploy-python-executable` with handling URLs and comments in `requirements.txt` have been fixed.

# 1.1.14

### New

- Large asset graphs can now be materialized in Dagit without needing to first enter an asset subset. Previously, if you wanted to materialize every asset in such a graph, you needed to first enter `*` as the asset selection before materializing the assets.

# 1.1.11

### New

- Requests that hit a `ReadTimeout` error will now retry in more cases.
- The “User Settings” section now opens in a dialog.
- [beta] Alert policies can now be set to notify on schedule / sensor tick failure. To learn more, check out the docs on alerting: https://docs.dagster.io/dagster-cloud/account/setting-up-alerts

### Bugfixes

- [dagit] Fixed search behavior on the Environment Variables page, which was incorrectly case-sensitive. Variables are also now sorted by “last update” time, with most-recently variables listed at the top.

# 1.1.10

### New

- Added support in Dagster Cloud Serverless for code locations using `requirements.txt` files with local package dependencies (for example, `../some/other/package`).

### Bugfixes

- Fixed an issue where setting `workspace.securityContext` in the agent Helm chart to override the security context of pods launched by the agent caused an error when starting up the agent.

# 1.1.8

### New

- [kubernetes] `securityContext` can now be set in the `dagsterCloudAgent` section of the Helm chart.
- [kubernetes] The agent Helm chart now includes a `serverK8sConfig` and `runK8sConfig` key that allows you to specify additional Kubernetes config that will be applied to each pod spun up by the agent to run Dagster code. Code locations can also be configured with a `server_k8s_config` or `run_k8s_config` dictionary with additional Kubernetes config in the pods that are spun up by the agent for that code location. See the [Kubernetes agent configuration reference](https://docs.dagster.io/dagster-cloud/deployment/agents/kubernetes/configuration-reference#per-location-configuration) for more information.
- [ecs] The ECS agent can now be configured with a `server_resources` and/or `run_resources` dictionary that will specify CPU and memory values for each task that is spun up by the agent to run Dagster code. Code locations can also be configured with a `server_resources` and/or `run_resources` dictionary that applies to each task spun up by the agent for that code location. See the [ECS agent configuration reference](https://docs.dagster.io/dagster-cloud/deployment/agents/amazon-ecs/configuration-reference) for more information.
- The Dagster Cloud agent will now re-upload information about each code location to Dagster Cloud from every time it starts up. Previously, the agent would only upload changes to Dagster Cloud when a code location was updated, meaning it was possible for the agent to become out of sync with what was shown in Dagit when the agent restarted.
- The `dagster-cloud serverless deploy-python-executable` command now supports a `--build-in-linux-docker` flag that builds the dependencies within a local Linux Docker container. This enables deploying source-only dependencies (sdists) from non Linux environment.
- When the Dagster Cloud agent stops heartbeating (for example, when it is being upgraded), dequeueing runs will pause until the agent is available again.
- Restored some metadata to the Code Locations tab in Dagster Cloud, including image, python file, module name, and commit hash.
- Added an `--asset-key` argument to the `dagster-cloud job launch` CLI command that allows the job launch to only materialize one or more specific assets from the job.
- `max_concurrent_dequeue`config has been added to the `run_queue` section of deployment config to allow slowing the rate at which queued runs are launched.

### Bugfixes

- Fixed an issue where the kubernetes agent was sometimes unable to move runs into a failed state when a run worker crashed or was interrupted by the Kubernetes cluster.
- A regression in retry handling for HTTP `429` responses released in `1.1.7` has been resolved.
- Cases where network errors were incorrectly reporting that they had tried and exhausted retries have been corrected.
- Fixed an issue where when adding or updating an environment variable, the change sometimes wasn’t reflected in branch deployments until they were redeployed.

# 1.1.7

### New

- [Non-isolated runs](https://docs.dagster.io/dagster-cloud/deployment/serverless#run-isolation) in Dagster Cloud Serverless now default to running at most 2 ops in parallel at once, to reduce the default memory usage of these runs. This number can be increased from the launchpad by configuring the `execution` key, for example:

```python
execution:
  config:
    multiprocess:
      max_concurrent: 4
```

- Run dequeue operations can now happen concurrently, improving the throughput of starting new runs.

### Bugfixes

- Fixed an issue where specifying a dictionary of proxies in the `dagster_cloud_api.proxies` key in an agent’s `dagster.yaml` file raised an error when proxies were also being set using environment variables.

# 1.1.6

### New

- Dagster Cloud Serverless can now deploy changes to your code using PEX files instead of building a new Docker image on each change, resulting in much faster code updates.
  - To update your existing GitHub workflows to use the PEX based fast deploys:
    1. Replace the YAML files in your `.github/workflows` directory with updated YAML files found in our [quickstart repository](https://github.com/dagster-io/quickstart-etl/tree/e07e944c7504a52b3d252553d51ad2085b4d5914/.github/workflows).
    2. Update the new YAML files and set `DAGSTER_CLOUD_URL` to the value in your original YAML files.
- The `dagster-cloud serverless` command now supports two new sub commands for fast deploys using PEX files:
  1. `dagster-cloud serverless deploy-python-executable` can be used instead of `dagster-cloud serverless deploy` to use the fast deploys mechanism. The existing `deploy` command is unchanged.
  2. `dagster-cloud serverless upload-base-image` can be used to upload a custom base image used to run code deployed using the above `deploy-python-executable` command. Using custom base images is optional.

  More details can be found in [our docs](https://docs.dagster.io/dagster-cloud/deployment/serverless).

- Runs that are launched from the Dagit UI in Dagster Cloud serverless can now be configured as either non-isolated or isolated. Non-isolated runs are for iterating quickly and trade off isolation for speed. Isolated runs are for production and compute heavy Assets/Jobs. For more information see [the docs.](https://docs.dagster.io/dagster-cloud/deployment/serverless#run-isolation)
- Email alerts from Dagster Cloud now include the name of the deployment in the email subject.

# 1.1.4

### New

- A handful of changes have been made to URLs in Dagit:
  - The `/instance` URL path prefix has been removed. E.g. `/instance/runs` can now be found at `/runs`.
  - The `/workspace` URL path prefix has been changed to `/locations`. E.g. the URL for job `my_job` in repository `foo@bar` can now be found at `/locations/foo@bar/jobs/my_job`.
- In Dagit, the “Workspace” navigation item in the top nav has been moved to be a tab under the “Deployment” section of the app, and is renamed to “Definitions”.

### Dependency Changes

- We’ve upgraded our `dagster/dagster-cloud-agent` Docker image’s base from `python:3.8.12-slim` to `python:3.8.15-slim` to patch [some vulnerabilities in the old base image](https://snyk.io/test/docker/python%3A3.8.12-slim).

# 1.1.1

### New

- A new “Environment Variables” section in the Deployment tab allows you to set environment variables that will be included whenever your Dagster code runs. See [the docs](https://docs.dagster.io/dagster-cloud/developing-testing/environment-variables-and-secrets) for more information. In order for environment variables to be included, your code must be using dagster version 1.0.17 or higher, and if you’re using a Hybrid agent, it must also be at dagster version 1.0.17 or higher.

### Bugfixes

- Fixed an issue where stack traces from errors that occurred within user code were sometimes not displayed in Dagit.
- Fixed an issue where failure during automatic retries before run creation would result in alerts not being sent. Now, if a failure occurs during the automatic retry of a run before the next run has been created, a specific alert will be sent.

### Documentation

- Updated [Environment variables and secrets documentation](https://docs.dagster.io/dagster-cloud/developing-testing/environment-variables-and-secrets) to include info about using the new “Environment Variables” section in the Deployment tab
- Added a dedicated guide for [setting environment variables using a Hybrid agent’s configuration](https://docs.dagster.io/dagster-cloud/developing-testing/setting-environment-variables-dagster-cloud-agents)

# 1.0.17

### Documentation

- Added documentation for [using environment variables](https://docs.dagster.io/dagster-cloud/developing-testing/environment-variables-and-secrets) in Dagster Cloud.
- Added a [configuration reference for the Docker agent](https://docs.dagster.io/dagster-cloud/deployment/agents/docker/configuration-reference).
- Added example configuration for environment variables and secrets to the [Kubernetes](https://docs.dagster.io/dagster-cloud/deployment/agents/kubernetes/configuration-reference#environment-variables-and-secrets) and [Amazon ECS](https://docs.dagster.io/dagster-cloud/deployment/agents/amazon-ecs/configuration-reference#environment-variables-and-secrets) agent configuration references.

# 1.0.16

### New

- [dagit] The new Overview and Workspace pages have been enabled for all users, after being gated with a feature flag for the last several releases. These changes include design updates, virtualized tables, and more performant querying.
- When running a Dagster Cloud agent, the Python logging configuration of the agent process can now be configured by passing in a `--agent-logging-config-path` option to the `dagster-cloud agent run` command. This config can also be set in the Dagster Cloud Helm chart using the `loggingConfig` key.
- Added a `dagster-cloud settings saml remove-identity-provider-metadata` command that can be used to reset the SAML configuration for an organization.
- You can now re-execute a run from failure in a Serverless deployment in Dagster Cloud without needing to define an IO manager

### Bugfixes

- Fixed the `createdBefore` filter on the run GraphQL endpoint.

# 1.0.15

### New

- The default Docker image for Serverless no longer runs `pip install --upgrade pip`.

### Experimental

- Non-isolated runs: Previously all runs launched in an isolated run environment. Opting in to this new feature adds a default option to the Launchpad to execute without isolation. The run will start faster, but with fewer compute resources. This is great for testing, but not recommended for compute or memory intensive production jobs. This will only apply to runs launched via the UI. Scheduled runs won't be affected. To enable:
  - Upgrade your agent to at least 1.0.15
  - In the UI, click on profile icon → User Settings → Enable non-isolated runs

# 1.0.14

### New

- The Amazon ECS agent will now re-use existing task definitions for the services that it spins up for each code location when the configuration for the service’s task definition has not changed. Previously, it would register a new task definition every time the service was re-deployed.

### Bugfixes

- Fixed an issue where Serverless images would error on the absence of a script `dagster_cloud_pre_install.sh` inside of the source folder.

# 1.0.13

### New

- The ECS Agent now shares a single task definition for every code location (instead of one task definition for the code location and another for any runs originating from that code location)
- `dagster-cloud serverless deploy` now blocks until the code location loads instead of returning immediately. This brings its behavior in line with other commands in the CLI and makes it safer to chain together multiple commands in a row (like launching a job after you deploy) without first needing to check if the deploy was successful.
- The deferred job snapshots option for workspace updates is now defaulted to on.

### Bugfixes

- [dagit] For users with the “New workspace page” feature flag enabled, code locations could not be added from the Deployment page. This has been fixed.

# 1.0.12

### New

- The ECS agent can now run in ECS clusters using EC2 capacity providers. See the [ECS agent docs](https://docs.dagster.io/dagster-cloud/deployment/agents/amazon-ecs/creating-ecs-agent-existing-vpc) for more information.
- The CloudFormation template for the ECS agent now configures multi-AZ support for the containers it launches.
- The default amount of time that a Dagster Cloud agent waits for user code to import being timing out has been increased from 60 seconds to 180 seconds, to avoid false positives when loading code with heavy imports or large numbers of assets.
- Added a deployment setting to configure the default role for SAML-provisioned users.

### Bugfixes

- The dagster-cloud CLI no longer lists branch deployments in the list of default deployments during setup.

# 1.0.11

### Bugfixes

- The GitHub setup flow for Serverless will now display an error if Actions builds are blocked from starting due to GitHub permissions.

# 1.0.10

### New

- When alerts are configured in Dagster Cloud on a job that also has automatic retries , the alert will now only fire if the final retry fails.
- Performance improvements to the Overview page.
- Job snapshot uploads now use a thread pool for parallelism.

### Bugfixes

- Fixed an issue where links to the compute logs in Dagit would sometimes fail to load.
- Improved user-facing error messages for Serverless GitHub setup.

# 1.0.9

### New

- Performance improvements for the Partitions page.
- A new scheme for workspaces updates has been added that improves performance in deployments with a large number of jobs. This is currently opt-in via the `defer_job_snapshots` setting in `user_code_launcher` config in dagster.yaml, or via `deferJobSnapshots` in the `workspace` section of the Dagster Cloud helm chart.

### Bugfixes

- Fixed an issue where assets sometimes didn’t appear in the Asset Catalog while in Folder view.
- Fixed an issue where the Create Token button would erroneously appear when revoking other users’ tokens.

# 1.0.8

### New

- [Kubernetes] Custom Kubernetes schedulers can now be applied to pods launched by the Dagster Cloud agent. To change the scheduler for all pods created by the agent, set `workspace.schedulerName` in the agent Helm chart. To set it for only the pods created as part of a particular code location, set the following configuration for the code location on the Workspace tab:

  ```
  container_context:
    k8s:
      scheduler_name: your-custom-schedule-name
  ```

  To change it for the agent, you'll still need to set `dagsterCloudAgent.schedulerName` in the agent Helm chart.

### Bugfixes

- Fixed an issue where the “Latest run” column on the Instance Status page sometimes displayed an older run instead of the most recent run.
- Added a pin to grpcio to address an issue with the recent 0.48.1 grpcio release that was sometimes causing Dagster code servers to hang.

# 1.0.7

### New

- [Kubernetes] The Agent Helm chart now supports `dagsterCloudAgent.schedulerName` and `workspace.schedulerName` for specifying a [custom Kubernetes scheduler](https://kubernetes.io/docs/tasks/extend-kubernetes/configure-multiple-schedulers/) for the Agent pod and workspace pods, respectively.
- [Kubernetes] The Agent Helm chart now supports pointing an agent at a list of deployments using the `dagsterCloud.deployments` field.

### Bugfixes

- Fixed an issue where GitHub Actions runs would trigger in an incorrect order during Serverless setup.

# 1.0.5

### Bugfixes

- Fixed an issue where login emails would not work for certain orgs

# 1.0.4

### New

- The top navigation of the Dagster Cloud UI now has a help menu with links to documentation and support.
- Added more user feedback to GitHub setup in Serverless new user experience.
- The Dagster Cloud usage page is now clarified to be in UTC time.
- Values have been added to the user-cloud helm chart for setting TTL (time to live) on user code servers managed by the agent.

### Bugfixes

- The `dagster-cloud serverless` command is no longer erroneously hidden from the help command list.
- Fixed an issue where inspecting asset groups in Code Previews did not lead to the correct link.

# 1.0.3

### New

- Introduced various UI improvements to the new organization onboarding flow.

# 1.0.2

### New

- The `dagster-cloud workspace` CLI now has a configurable Agent heartbeat timeout. The CLI will logspew every few seconds while waiting for the Agent to sync a code location.
- When a code location is added or updated, a notification will appear in Dagit, and the Workspace tab will automatically refresh.
- Added additional retries when the ECS agent encounters a problem spinning up a new service.

### Bugfixes

- Trying to add a code location with an empty name now throws an error message.
- Fixed an issue where the alert policy UI would not allow creating an alert policy with no tags, which targets all jobs.

### Documentation

- The docs have moved! All Dagster docs now live at `docs.dagster.io.` [Click here to check out the new and improved Cloud docs](https://docs.dagster.io/dagster-cloud).

# 1.0.1

### Documentation

- The [Dagster Cloud docs](https://docs.dagster.io/dagster-cloud) now live alongside all the other Dagster docs! Check them out by nagivating to Deployment > Cloud.

# 1.0.0

### New

- Performance improvements when the Dagster Cloud agent is deploying more than one code location at the same time.
- The default timeout for runs to start has been increased from 5 minutes to 10 minutes. We had observed that ECS tasks often would exceed timeout when pulling a large image.

# 0.15.8

### New

- Branch Deployments are now ordered by their most recent commit time on the Deployments tab.
- You can now access the name of the current Dagster Cloud deployment within your Dagster code by checking the `DAGSTER_CLOUD_DEPLOYMENT_NAME` environment variable. You can use this to change the behavior of your code depending on the deployment in which it is running.

# 0.15.7

### Bugfixes

- Fixed an issue where launching a run with just whitespace in the Launchpad would create an error.
- Fixed an issue where creating a code location that started with a numeric character failed to load when using the Kubernetes agent.

# 0.15.6

### New

- Improved query performance for loading the Asset Graph in Dagit.
- The ECS agent is now more resilient to ECS’s eventual consistency model. In your dagster.yaml, you can configure how long ECS polls against AWS ECS API endpoints by setting:

  ```
  user_code_launcher:
    module: dagster_cloud.workspace.ecs
      class: EcsUserCodeLauncher
      config:
        timeout: 180 # default: 300
  ```

  And you can configure how long ECS will retry a failed AWS ECS API endpoint by setting:

  ```
  user_code_launcher:
    module: dagster_cloud.workspace.ecs
      class: EcsUserCodeLauncher
      config:
        grace_period: 20 # default: 10
  ```

- The Dagster Cloud API may start returning HTTP response code 429 when it receives an unusually large number of requests in a short period of time. The HTTP response will include a `Retry-After` header indicating the number of seconds to wait before retrying the request.

### Bugfixes

- Fixed an issue where the Kubernetes agent didn’t work correctly when setting `container_context.namespace` to run code locations in different Kubernetes namespaces.

# 0.15.5

### New

- The dagster-cloud CLI now supports adding a single code location from a file containing a list of locations by specifying the `--location-name` parameter.

# 0.15.3

### New

- User code servers now support a configurable time-to-live (TTL). The agent will spin down any user code servers that haven’t served requests recently and will spin them back up the next time they’re needed. You can use this TTL to save compute cost because your user code servers will spend less time sitting idle. [You can configure TTL](https://docs.dagster.cloud/agents/agent-settings#enabling-user-code-server-ttl) in your agent’s `dagster.yaml`:

```yaml
user_code_launcher:
  config:
    server_ttl:
      enabled: true
      ttl_seconds: 7200 # 2 hours
```

- When viewing agent and user tokens under the settings page, tokens are now sorted by latest creation date.

### Bugfixes

- When configuring alert policies, all inputs are now validated before submission.
- When copying an agent related error message, the original error and stack trace are now included.

# 0.15.2

### New

- Added [Terms of Service](https://dagster.io/terms) to Dagster Cloud.
- Organization admins can now be managed from the Cloud permissions page. For more information, see the Cloud [RBAC docs](https://docs.dagster.cloud/auth#role-based-access-controls).

# 0.15.1

### Bugfixes

- Fixed an issue where an empty list of email addresses could be configured on an email alert policy.
- When an agent is accidentally configured with a user token rather than an agent token, an informative exception is now displayed.
- Fixed an issue where jobs using [memoization](https://docs.dagster.io/guides/dagster/memoization#versioning-and-memoization) sometimes did not launch in Dagster Cloud.

# 0.15.0

### New

- The new features announced in the [Dagster 0.15.0 release](https://github.com/dagster-io/dagster/releases/tag/0.15.0) are also available to Dagster Cloud users. In particular, software-defined assets are now marked fully stable and are ready for prime time - we recommend using them whenever your goal using Dagster is to build and maintain data assets.
- The [ECS agent CloudFormation template](https://docs.dagster.cloud/agents/ecs/setup#provisioning-using-cloudformation) is now versioned, allowing you to fix a specific version of the agent.
- You can now configure job-level retries to re-execute the full run rather than just failed Ops by setting the `dagster/retry_strategy` tag to `ALL_STEPS`. See [the docs](https://docs.dagster.io/deployment/run-retries) for more information.

# 0.14.20

### New

- The Kubernetes agent and ECS agent can now include arbitrary environment variables in the containers that they create to run Dagster code. You can configure environment variables by setting `env_vars` in the `dagster.yaml` file for the agent, which will apply them to all code locations. You can also set `env_vars` on individual code locations. For example, to configure a code location to always set `FOO_ENV_VAR` to `bar_value` when creating Kubernetes pods, you can set this config in the Workspace tab or via the Dagster Cloud GitHub action:

```yaml
location_name:my_location
image: my_repo:my_tag
code_source:
  package_name: my_package
container_context:
  k8s:
    env_vars:
      - FOO_ENV_VAR=bar_value
      - WILL_LOAD_ENV_VAR_FROM_PROCESS_IF_VALUE_NOT_SET
```

- Introduced a checklist to guide new organizations in setting up their Cloud deployment.

- Users with Editor or Admin permissions can now edit [deployment settings](https://docs.dagster.cloud/guides/managing-deployments#deployment-settings) from the Dagster Cloud UI, by clicking on the gear icon next to the deployment name in the deployment switcher in the upper-right corner of the screen.

### Bugfixes

- Fixed a bug where renaming an alert created a new alert.
- Attempting to create a deployment with a duplicate name now produces a clear error.

# 0.14.19

### New

- Added a new `dagster-cloud-cli` package. You can install this package if you want to interact with the CLI without also installing many of the additional packages that `dagster-cloud` depends on, simplifying installation on M1 Macs.
- [Deployment settings](https://docs.dagster.cloud/guides/managing-deployments#deployment-settings) can now be configured using a YAML editor in the Dagster Cloud UI.

### Bugfixes

- Fixed an issue where a user could set their run coordinator’s `max_concurrent_runs` to be negative.
- [dagit] Alerts can now be configured on a deployment with no jobs.

# 0.14.17

### New

- The Backfill page in Dagit now loads much faster when there are backfills with large numbers of runs.

### Bugfixes

- Added a pin to version 3 of the `protobuf` library in Dagster Cloud, due to a breaking change in version 4 that was causing an error on startup.
- Fixed an issue where configuration errors while launching a run sometimes didn’t display a useful explanation for why the configuration was invalid.
- Fixed an issue where Dagster Cloud would sometimes fail to fire failure alerts due to external rate limits.

# 0.14.16

### Bugfixes

- Fixed an issue where the backfills page would fail to load when a deployment contained backfills from a code location that was no longer in the workspace.
- Fixed an issue where certain types of failures caused alerts to not fire.

# 0.14.15

### New

- You can now set up automatic retries for Jobs. Set a default for all Jobs in your deployment using `run_retries.max_retries` in [Deployment Settings](https://docs.dagster.cloud/guides/managing-deployments#configuring-the-settings), or set it per run using the `dagster/max_retries` tag. When configured, failed runs will be reexecuted from failure up to the maximum number of times.
- When a Slack alert is sent for a run triggered by a sensor or schedule, the alert now contains a URL link to the sensor or schedule.

### Bugfixes

- Fixed github login setting misleading user display names when using multiple emails.

# 0.14.14

### New

- Alert Policies can now be edited in Dagit. To view and configure the alert policies for your deployment, click on the profile picture in the upper-right corner of Dagit, navigate to the Cloud Settings page, and click on the Alerts tab. https://docs.dagster.cloud/guides/alerts

# 0.14.13

### New

- When using the Kubernetes agent, you can now supply a `resources` key under `workspace` that will apply resource requirements to any pods launched by the agent. For example:

```yaml
workspace:
  resources:
    limits:
      cpu: 100m
      memory: 128Mi
    requests:
      cpu: 100m
      memory: 128Mi
```

You can also vary the resource requirements for pods from different code locations by setting config in the Workspace tab. For example:

```yaml
location_name: test-location
image: dagster/dagster-cloud-template:latest
code_source:
  package_name: dagster_cloud_template
container_context:
  k8s:
    resources:
      limits:
        cpu: 100m
        memory: 128Mi
      requests:
        cpu: 100m
        memory: 128Mi
```

- When upgrading the Kubernetes agent using the Helm chart, the previous agent pod will now fully terminate before the new agent spins up.
- Descriptions can now be added to distinguish your user and agent tokens on the Cloud Settings page.
- Using the `dagster-cloud` CLI to add or update a code location, CLI options can now override location config from a specified file. For example, `dagster-cloud workspace add-location --from-file location.yaml --image dagster/dagster-cloud-examples:64c9c2`.

### Bugfixes

- Fixed an issue where [code previews](https://docs.dagster.cloud/guides/code-previews) would sometimes fail to load if a working directory was not explicitly set.

# 0.14.12

### Bugfixes

- Fixed an issue where the Launchpad in Dagit sometimes incorrectly launched in an empty state.

# 0.14.11

### Bugfixes

- Fixed an issue where Dagit sometimes showed a generic "Internal Server Error" message when launching a run, instead of a more detailed error message.

# 0.14.10

### New

- Configuring tags for an alert policy is now optional. When omitted, the alert policy will apply to all runs in the deployment that have matching events.
- Added the ability to fetch workspace configuration using the `dagster-cloud` CLI using `dagster-cloud workspace pull`.

### Bugfixes

- [dagit] Fixed an issue where if you used the same repo name/job name in two different deployments their launchpad configs would be shared. Now they’re separate.
- [dagit] Fixed an issue where attempting to add a code location with a name that already exists would result in an error. Validation now occurs to prevent the user from doing this.

# 0.14.9

### New

- You can now set a `container_context` key in your code locations in the Workspace tab, which lets you set configuration for a specific execution environment (K8s, Docker, or ECS) for that code location. Previously, this configuration could only be set in the `dagster.yaml` file for your agent, which required you to share it across code locations, and restart your agent whenever it changed. For example, you can specify that a code location should include a secret called `my_secret` and run in a K8s namespace called `my_namespace` whenever the Kubernetes agent creates a pod for that location:

```
location_name: test-location
image: dagster/dagster-cloud-template:latest
code_source:
  package_name: dagster_cloud_template
container_context:
  k8s:
    namespace: my_namespace
    env_secrets:
      - my_secret
```

For more information, see https://docs.dagster.cloud/guides/adding-code#environment-specific-config.

- [Alert policies](https://docs.dagster.cloud/guides/alerts) can now be viewed in Dagit. You can see the list of alert policies in a tab under Cloud Settings.

# 0.14.8

### New

- Dagster Cloud Slack notifications now display message previews.

### Bugfixes

- Fixed an issue where event logs displayed that a Slack notification had failed when they actually succeeded.

# 0.14.7

### New

- Email alerts now include the run’s start and end time.
- Dagster Cloud now displays more verbose event logging when an alert succeeds or fails.
- Added links to Dagster Cloud changelog and status page in the login page.

### Bugfixes

- Fixed an issue where alert policy names were required to be unique across deployments in an organization.

### Documentation

- Added instructions to display your alert policies using the Dagster Cloud CLI.

# 0.14.6

### New

- Added the ability to add or update single code locations with a YAML file in the dagster-cloud CLI. For more information, see the adding code to Dagster Cloud docs (https://docs.dagster.cloud/guides/adding-code#using-the-dagster-cloud-cli).
- When Dagster Cloud is temporarily unavailable due to scheduled maintenance, jobs that are running when the maintenance starts will wait for the maintenance to conclude and then continue execution, instead of failing.
- Alert policies are now supported in Dagster Cloud. Alert policies define which jobs will trigger an alert, the conditions under which an alert will be sent, and how the alert will be sent.

  An alert policy includes a set of configured tags. Only jobs that contain all the tags for a given alert policy are eligible for that alert. Additionally, an alert policy includes a set of conditions under which an alert will be triggered. For example, the alert can be triggered to fire on job failure, job success, or both events. Finally, an alert policy specifies where the alert will be sent. Currently, we support Slack and email as targets for an alert.

  See https://docs.dagster.cloud/guides/alerts for more details.

# 0.14.4

### New

- You can now [set secrets with the ECS Agent using the same syntax that you use to set secrets in the ECS API](<(https://docs.dagster.io/0.14.4/deployment/guides/aws#secrets-management-in-ecs)>).
- The ECS Agent now raises the underlying ECS API failure if it cannot successfully start a task or service.
- You can now delete a code location without running an agent.

Bugfixes

- Fixed a Python packaging issue which caused the `dagster_cloud_examples` package to fail to load when used with the local agent.

Documentation

- Document a strategy for developing your Dagster jobs locally using Dagster Cloud and the DockerUserCodeLauncher.
- Document how to grant AWS IAM permissions to Dagster K8s pods using service accounts.

# 0.14.3

### New

- [K8s] The agent now monitors active runs. Failures in the underlying Kubernetes Job (e.g. an out of memory error) will now be reported in Dagit.

### Bugfixes

- Fixed an issue where the favicon didn’t update to reflect success, pending, or failure status when looking at a job’s run page.

# 0.14.2

### New

- Individual `context.log` messages which appear in the Dagster event log will now be truncated after 50,000 characters. The full contents of these messages remain available in the compute logs tab. For large logs, we recommend logging straight to stdout or stderr rather than using `context.log`.

### Bugfixes

- Added a missing IAM permission to the ECS Agent Cloudformation template that was preventing the ECS agent from being able to terminate runs.

### Documentation

- Added a new [guide](https://docs.dagster.cloud/guides/adding-code) to the Dagster Cloud docs covering how to add and update code.

# 0.14.1

### Bugfixes

- Sensors that have a default status can now be manually started. Previously, this would fail with an invariant exception.

# 0.14.0

### New

- Added a button to test out Dagster Cloud with a sample code location when you go to the Workspace tab on an empty Deployment.
- Added quick links to log in to your organizations from https://dagster.cloud (must be signed in)
- [K8s] Added an `imagePullGracePeriod` field to the helm chart that tells the agent how long to allow errors while pulling an image before failing. For example:

```yaml
# values.yaml
workspace:
  imagePullGracePeriod: 60
```

- [K8s] The agent container can now run as a non-root user. The `docker.io/dagster/dagster-cloud-agent` image includes a dagster user with ID `1001` that can be assumed by setting `podSecurityContext` in your Helm values:

```yaml
# values.yaml
podSecurityContext:
  runAsUser: 1001
```

### Bugfixes

- Fixed an issue where run status sensors sometimes failed to trigger.
- [ECS] Fixed an issue where the Cloudformation template for setting up an ECS agent would sometimes fail to spin up tasks with an AWS Secretsmanager permission error.
- Fixed an issue where the agent sometimes left old user code servers running after the server failed to start up.
- Fixed an issue where the agent sometimes stopped sending heartbeats while it was in the middle of starting up a new user code server.
- Fixed an issue where an erroring code location would not show as updating when redeploying.

### Documentation

- Added a new guide to configuring the Kubernetes agent (https://docs.dagster.cloud/agents/kubernetes/configuring).
- Updated documentation to show adding new code locations through Dagit.

# 0.13.19

### New

- The Dagster Cloud workspace page now allows creating, deleting, and updating code locations from Cloud Dagit in addition to via the CLI.
- The ECS agent can now override the `secrets_tag` parameter to None, which will cause it to not look for any secrets to be included in the tasks that the agent creates. This can be useful in situations where the agent does not have permissions to query AWS Secretsmanager
- Added a `dagit_url` property to the DagsterInstance in Dagster Cloud that can be used to reference the Dagster Cloud Dagit URL within ops and sensors.
- Introduced a path to run the local Dagster Cloud agent ephemerally without specifying a `dagster.yaml`, by using CLI arguments.
- Added the ability to configure [Python logging](https://docs.dagster.io/concepts/logging/python-logging#python-logging) in the Kubernetes agent helm chart. For example:

```
pythonLogs:
   # The names of python loggers that will be captured as Dagster logs
   managedPythonLoggers:
     - foo_logger
   # The log level for the instance. Logs emitted below this severity will be ignored.
   # One of [NOTSET, DEBUG, INFO, WARNING, WARN, ERROR, FATAL, CRITICAL]
   pythonLogLevel: INFO
   # Python log handlers that will be applied to all Dagster logs
   dagsterHandlerConfig:
     handlers:
       myHandler:
         class: logging.FileHandler
         filename: "/logs/my_dagster_logs.log"
         mode: "a"
```

### Bugfixes

- Added a missing AWS secretsmanager permission to the example CloudFormation template for creating an ECS agent.
- Improved dagster-cloud CLI web authentication error messages on the client and server, including troubleshooting steps and instructions on alternative token authentication.
- Fixed an issue where deleting a deployment from Dagit would sometimes fail.

### Documentation

- Added a setup guide for SAML SSO using PingOne.
- Added a documentation page detailing switching, creating, and deleting deployments.

# 0.13.18

### New

- Secrets in the ECS Agent: When using Dagster Cloud in ECS, you can specify a list of AWS Secrets Manager ARNs to include in all tasks that the agent spins up. Any secrets that are tagged with the key “dagster” in AWS Secrets Manager (or a custom key that you specify) will also be included in all tasks. You can customize the secrets in your ECS Agent in your `dagster.yaml` file as follows:

```
user_code_launcher:
  module: dagster_cloud.workspace.ecs
  class: EcsUserCodeLauncher
  config:
    cluster: your-cluster-name
    subnets:
      - your-subnet-name
    service_discovery_namespace_id: your-service-discovery-namespace-id
    execution_role_arn: your-execution-role-arn
    log_group: your-log-group
    secrets_tag: "my-tag-name"
    secrets:- "arn:aws:secretsmanager:us-east-1:1234567890:secret:MY_SECRET"`
```

- Added support in Dagster Cloud for disabling compute logs, which display the stdout/stderr output from your Dagster jobs within Dagit. When using the Dagster Cloud helm chart, by setting `Values.computeLogs.enabled` to false, users can prevent compute logs from being forwarded into Dagster Cloud. Logging configured separately from Dagster on Kubernetes will continue to work, but won’t be viewable in the Dagster Cloud UI.

### Bugfixes

- Fixed an issue where omitting the Dagster Cloud agent endpoint when installing the Kubernetes agent using the helm chart would sometimes cause the agent to fail to start. The agent endpoint is no longer a required field on the helm chart.
- Fixed an issue with dagster-cloud CLI web authentication where users who did not have an available user token could not be authenticated.

### Documentation

- Added a “Customizing your agent” section to the docs, including documentation on how to disable compute logging when manually authoring an agent’s `dagster.yaml`.

# 0.13.17

### New

- Dagster Cloud now supports authenticating with Github. Verified emails associated with your Github user can be used for login authorization for Dagster Cloud.
- Various improvements to the Dagster Cloud CLI.
  - You can now display your version of Dagster Cloud by invoking `dagster-cloud --version`.
  - Enabled `-h` as another alias for `--help`
  - If you’ve configured a default organization, deployment, and token using `dagster-cloud config setup`, your default values will now show in the help text for any command.
  - Installing completions using `--install-completion` no longer requires you to pass the name of your shell.

### Documentation

- The Dagster Cloud tutorial at https://docs.dagster.cloud has been streamlined and rewritten.
- Added documentation for running multiple agents for the same Dagster Cloud deployment at https://docs.dagster.cloud/deployment/multiple-agents.
- Added documentation for installing completions to the dagster-cloud CLI at https://docs.dagster.cloud/dagster-cloud-cli#completions.

# 0.13.16

## Dagster Cloud

### New

- `dagster-cloud config setup` now allows the user to authenticate the CLI by logging in through the browser.

### Bugfixes

- When uploading SAML metadata via the `dagster-cloud` CLI, a deployment no longer needs to be specified.

## Agent

### New

- If your agent’s Dagster Cloud version is >=0.13.15, its version will now surface on your Dagster Cloud instance status page.
- The Kubernetes agent can now specify a dictionary of labels that will be applied to the pods spun up by the agent. Here is an example `values.yaml` snippet that adds pod labels:

  ```
  workspace:
    labels:
      my_label_key: my_label_value
  ```

# 0.13.14

## Dagster Cloud

### New

- Deployment settings (run queue configuration, run start timeouts) can now be configured via the `dagster-cloud` CLI. For example: `dagster-cloud deployment settings set-from-file example-settings.yaml`. These settings will soon be available to configure within Dagit as well as the CLI.

  ```
  # example-settings.yaml
  run_queue:
    max_concurrent_runs: 10
    tag_concurrency_limits: []
  run_monitoring:
    start_timeout_seconds: 300
  ```

- There is now documentation to set up SAML SSO for Google Workspace. See https://docs.dagster.cloud/auth/google-workspace for details.

## Agent

### New

- Containers created by the Docker agent can now be configured with any configuration that’s available on the [`Container.run` call in the Docker Python client](https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run). For example, to ensure that containers are automatically removed when they are finished running, you can configure your `dagster.yaml` as follows:

  ```
  user_code_launcher:
    module: dagster_cloud.workspace.docker
    class: DockerUserCodeLauncher
    config:
      container_kwargs:
        auto_remove: true
  ```

- Logging is now emitted from the `dagster_cloud` logger.

# 0.13.13

## Dagster Cloud

### New

- Performance improvements in Dagit on the Run Viewer page, Runs page, and Workspace page.
- The Status page in Dagit now displays more information about each agent that is currently running.
- When the agent is down, the scheduler will now wait for the agent to be available again before running schedule ticks, instead of marking the tick as failed.
- The Dagster Cloud Github Action now supports creating Dagit previews of your Dagster code when you create a pull request. To set up this feature, please see the [documentation](https://docs.dagster.cloud/deployment/code-previews).
- The `dagster-cloud` CLI will now notify the user if their Dagster Cloud agent is not running when attempting to modify workspace locations, instead of polling for the agent to sync the update.
- The `dagster-cloud configure` CLI command has been renamed to `dagster-cloud config setup`.
- The default number of jobs that can run at once per deployment has in raised to 25 instead of 10. This value will become configurable per-deployment in an upcoming release.

### Bugfixes

- Fixed an issue where the Kubernetes agent would sometimes time out while creating a new code deployment on startup.
- Fixed an issue where importing local modules in job code would sometimes fail to load unless you explicitly set a working directory via the `dagster-cloud` CLI.
- Fixed an issue where switching organizations could cause a GraphQL error during the `dagster-cloud` CLI configuration process.
- Fixed a bug where trying to load compute logs in Dagit for a step that hadn’t yet finished displayed an error.

## Agent

### New

- Agents can now be optionally assigned a label with the `dagster_cloud_api.agent_label` configuration option in the `dagster.yaml` file.
- ECS agent CloudFormation templates now append part of the stack ID to the Service Discovery name to prevent naming conflicts when launching multiple agents for the same deployment.

# 0.13.12

## Agent

### New

- [ECS] Previously, ECS tasks and services created by the ECS agent always used the VPC’s default security group. Now, you can configure it to use a different list of security groups in your `dagster.yaml`.
- When configuring code locations in Dagster Cloud, you can now specify all the same configuration options that you can when specifying a workspace in open-source Dagster. Run `dagster-cloud workspace add-location --help` to see the full set of available options.

## Dagster Cloud

### Bugfixes

- Fixed an issue where the “View Configuration...” link on schedules went to an invalid URL in Dagster Cloud.
- Fixed an issue where Dagster Cloud links in the Okta store were sometimes invalid.
- Fixed an issue where some externally-launched SAML logins lacking URL parameters would cause an error.
- Fixed an issue where schedule ticks would sporadically timeout in Cloud (requires upgrading the agent to 0.13.12)
- Fixed an issue where checking the “Force Termination Immediately" checkbox in Dagit would cancel the run without attempting to clean up the computational resources created by that run.
- Fixed an issue where Dagit would sometimes require the “Force Termination Immediately” checkbox to be set when terminating a run, instead of offering it as an option.

# 0.13.11

## Dagster Cloud

### New

- Email alerts now display basic metadata about the failed run, including the number of steps succeeded, steps failed, and a link to the run in your Dagster Cloud instance.
- Improved Dagit page loading times for repositories with many schedules or sensors.
- The `dagster-cloud` CLI now correctly exits on keyboard interrupt.

## Agent

### Bugfixes

- [ECS] Ensured that the ECS agent properly cleans up ServiceDiscovery services when the agent spins down. Previously, this left orphaned services which would prevent CloudFormation teardown from deleting the associated ServiceDiscovery namespace.

## CI/CD GitHub Action

### New

- Support specifying a Docker target stage when building multistage Dockerfiles.
