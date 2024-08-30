---
title: "Hybrid agent settings"
displayed_sidebar: "dagsterPlus"
sidebar_position: 60
sidebar_label: "Settings"
---

# Dagster+ Agent configuration reference
You can configure your Dagster+ agent the same way you configure any [Dagster Instance](https://docs.dagster.io/deployment/dagster-instance) - with a `dagster.yaml` file. This reference describes all available configuration options. For the most common configurations, see our [Dagster+ Agent guides](dagster-plus/deployment/hybrid).
|Config Path|Type|Required|Default|Description|
|--|--|--|--|--|
dagster_cloud_api.agent_token|StringSourceType|True||Dagster+ agent api token.
dagster_cloud_api.agent_label|StringSourceType|False||Custom label visible in the Dagster+ UI.
dagster_cloud_api.deployment|ScalarUnion.String-Array.String|False||Handle requests for a single deployment.
dagster_cloud_api.deployments|Array.StringSourceType|False||Handle requests for multiple deployments
dagster_cloud_api.branch_deployments|BoolSourceType|False|False|Handle requests for all branch deployments (can be combined with `deployment` or `deployments`)
dagster_cloud_api.timeout|Noneable.IntSourceType|False|60|How long before a request times out against the Dagster+ API servers.
dagster_cloud_api.retries|IntSourceType|False|6|How many times to retry retriable response codes (429, 503, etc.) before failing.
dagster_cloud_api.backoff_factor|Float|False|0.5|Exponential factor to back off between retries.
dagster_cloud_api.method|StringSourceType|False|POST|Default HTTP method.
dagster_cloud_api.verify|Bool|False|True|If False, ignore verifying SSL.
dagster_cloud_api.headers|Permissive|False|{}|Custom headers.
dagster_cloud_api.cookies|Permissive|False|{}|Custom cookies.
dagster_cloud_api.proxies|Map.String.String|False||Custom proxies.
dagster_cloud_api.socket_options|Noneable.Array.Array.Any|False|None|Custom socket options.
user_code_launcher.module|String|True||
user_code_launcher.class|String|True||
user_code_launcher.config|Permissive|False|{}|
isolated_agents.enabled|Bool|False|False|
agent_queues.include_default_queue|Bool|False|True|
agent_queues.additional_queues|Array.String|False||
# User code launcher configuration reference
User code launchers control how code servers are managed by the Dagster+ agent. For example, whether to manage each code server as its own container or not.
<Tabs groupId="user-code-launchers">
<TabItem value="kubernetes" label="Kubernetes">
|Config Path|Type|Required|Default|Description|
|--|--|--|--|--|
user_code_launcher.config.env_config_maps|Noneable.Array.StringSourceType|False||A list of custom ConfigMapEnvSource names from which to draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/#define-an-environment-variable-for-a-container
user_code_launcher.config.env_secrets|Noneable.Array.StringSourceType|False||A list of custom Secret names from which to draw environment variables (using ``envFrom``) for the Job. Default: ``[]``. See:https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
user_code_launcher.config.service_account_name|Noneable.StringSourceType|False||The name of the Kubernetes service account under which to run.
user_code_launcher.config.env_vars|Noneable.Array.String|False||A list of environment variables to inject into the Job. Each can be of the form KEY=VALUE or just KEY (in which case the value will be pulled from the current process). Default: ``[]``. See: https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#configure-all-key-value-pairs-in-a-secret-as-container-environment-variables
user_code_launcher.config.volume_mounts|Array.Permissive.d74633764cf9c37a0754dd99361d5d93635f9684|False|[]|A list of volume mounts to include in the job's container. Default: ``[]``. See: https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volumemount-v1-core
user_code_launcher.config.volumes|Array.Permissive.4f22714b0385d03e44bea13cecbbcb678c84293c|False|[]|A list of volumes to include in the Job's Pod. Default: ``[]``. For the many possible volume source types that can be included, see: https://v1-18.docs.kubernetes.io/docs/reference/generated/kubernetes-api/v1.18/#volume-v1-core
user_code_launcher.config.image_pull_secrets|Noneable.Array.Shape.0534824752960af13af95e516c38700993959fe5|False||Specifies that Kubernetes should get the credentials from the Secrets named in this list.
user_code_launcher.config.labels|Permissive|False||Labels to apply to all created pods. See: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels
user_code_launcher.config.resources|Noneable.Shape.53ad09eb6c429a2d9a30d8b6a55a5a94d49835a1|False||Compute resource requirements for the container. See: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
user_code_launcher.config.scheduler_name|StringSourceType|False||
user_code_launcher.config.security_context|Permissive|False||Security settings for the container. See:https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-capabilities-for-a-container
user_code_launcher.config.dagster_home|StringSourceType|True||
user_code_launcher.config.instance_config_map|StringSourceType|True||
user_code_launcher.config.kubeconfig_file|StringSourceType|False||
user_code_launcher.config.deployment_startup_timeout|IntSourceType|False|300|Timeout when creating a new Kubernetes deployment for a code server
user_code_launcher.config.server_process_startup_timeout|IntSourceType|False|180|Timeout when waiting for a code server to be ready after it is created
user_code_launcher.config.image_pull_grace_period|IntSourceType|False|30|
user_code_launcher.config.pull_policy|Noneable.StringSourceType|False||Image pull policy to set on launched Pods.
user_code_launcher.config.namespace|StringSourceType|False|default|
user_code_launcher.config.run_k8s_config.container_config|Permissive|False|{}|
user_code_launcher.config.run_k8s_config.pod_template_spec_metadata|Permissive|False|{}|
user_code_launcher.config.run_k8s_config.pod_spec_config|Permissive|False|{}|
user_code_launcher.config.run_k8s_config.job_config|Permissive|False|{}|
user_code_launcher.config.run_k8s_config.job_metadata|Permissive|False|{}|
user_code_launcher.config.run_k8s_config.job_spec_config|Permissive|False|{}|
user_code_launcher.config.server_k8s_config.container_config|Permissive|False|{}|
user_code_launcher.config.server_k8s_config.pod_spec_config|Permissive|False|{}|
user_code_launcher.config.server_k8s_config.pod_template_spec_metadata|Permissive|False|{}|
user_code_launcher.config.only_allow_user_defined_k8s_config_fields.container_config|Map.String.Bool|False||
user_code_launcher.config.only_allow_user_defined_k8s_config_fields.pod_spec_config|Map.String.Bool|False||
user_code_launcher.config.only_allow_user_defined_k8s_config_fields.pod_template_spec_metadata|Map.String.Bool|False||
user_code_launcher.config.only_allow_user_defined_k8s_config_fields.job_metadata|Map.String.Bool|False||
user_code_launcher.config.only_allow_user_defined_k8s_config_fields.job_spec_config|Map.String.Bool|False||
user_code_launcher.config.only_allow_user_defined_k8s_config_fields.namespace|Bool|False||
user_code_launcher.config.only_allow_user_defined_env_vars|Array.String|False||List of environment variable names that are allowed to be set on a per-run or per-code-location basis - e.g. using tags on the run. 
user_code_launcher.config.code_server_metrics.enabled|Bool|False|False|
user_code_launcher.config.agent_metrics.enabled|Bool|False|False|
user_code_launcher.config.server_ttl.full_deployments.enabled|BoolSourceType|True||Whether to shut down servers created by the agent for full deployments when they are not serving requests
user_code_launcher.config.server_ttl.full_deployments.ttl_seconds|IntSourceType|False|86400|If the `enabled` flag is set , how long to leave a server running for a once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.branch_deployments.ttl_seconds|IntSourceType|False|86400|How long to leave a server for a branch deployment running once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.max_servers|IntSourceType|False|25|In addition to the TTL, ensure that the maximum number of servers that are up at any given time and not currently serving requests stays below this number.
user_code_launcher.config.server_ttl.enabled|BoolSourceType|False||Deprecated - use `full_deployments.enabled` instead
user_code_launcher.config.server_ttl.ttl_seconds|IntSourceType|False||Deprecated - use `full_deployments.ttl_seconds` instead
user_code_launcher.config.defer_job_snapshots|BoolSourceType|False|True|Do not include full job snapshots in the workspace snapshot, upload them separately if they have not been previously uploaded.
user_code_launcher.config.upload_snapshots_on_startup|BoolSourceType|False|True|Upload information about code locations to Dagster Cloud whenever the agent starts up, even if the code location has not changed since the last upload.
user_code_launcher.config.requires_healthcheck|BoolSourceType|False|False|Whether the agent update process expects a readiness sentinel to be written before an agent is considered healthy. If using zero-downtime agent updates, this should be set to True.
</TabItem>
<TabItem value="ecs" label="Amazon ECS">
|Config Path|Type|Required|Default|Description|
|--|--|--|--|--|
user_code_launcher.config.cluster|StringSourceType|True||
user_code_launcher.config.subnets|Array.StringSourceType|True||
user_code_launcher.config.security_group_ids|Array.StringSourceType|False||
user_code_launcher.config.execution_role_arn|StringSourceType|True||
user_code_launcher.config.task_role_arn|StringSourceType|False||
user_code_launcher.config.log_group|StringSourceType|True||
user_code_launcher.config.service_discovery_namespace_id|StringSourceType|True||
user_code_launcher.config.secrets|Array.ScalarUnion.String-Shape.66af04ecd8c59f52910dbbd9a9e035809de69d6a|False||An array of AWS Secrets Manager secrets. These secrets will be mounted as environment variabls in the container. See https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Secret.html.
user_code_launcher.config.secrets_tag|Noneable.StringSourceType|False||AWS Secrets Manager secrets with this tag will be mounted as environment variables in the container.
user_code_launcher.config.env_vars|Array.StringSourceType|False||List of environment variable names to include in the ECS task. Each can be of the form KEY=VALUE or just KEY (in which case the value will be pulled from the current process)
user_code_launcher.config.server_process_startup_timeout|IntSourceType|False|180|Timeout when waiting for a code server to be ready after it is created. You might want to increase this if your ECS tasks are successfully starting but your gRPC server is timing out.
user_code_launcher.config.ecs_timeout|IntSourceType|False|300|How long (in seconds) to poll against ECS API endpoints. You might want to increase this if your ECS tasks are taking too long to start up.
user_code_launcher.config.ecs_grace_period|IntSourceType|False|30|How long (in seconds) to continue polling if an ECS API endpoint fails (because the ECS API is eventually consistent)
user_code_launcher.config.launch_type|EcsLaunchType|False|FARGATE|What type of ECS infrastructure to launch the run task in. See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/launch_types.html
user_code_launcher.config.code_server_metrics.enabled|Bool|False|False|
user_code_launcher.config.agent_metrics.enabled|Bool|False|False|
user_code_launcher.config.server_resources|Permissive.9b8ec62d3a159a951e8d067e608da6521139ba90|False|{}|
user_code_launcher.config.run_resources|Permissive.9b8ec62d3a159a951e8d067e608da6521139ba90|False|{}|
user_code_launcher.config.runtime_platform.cpuArchitecture|StringSourceType|False||
user_code_launcher.config.runtime_platform.operatingSystemFamily|StringSourceType|False||
user_code_launcher.config.volumes|Array.Permissive.1f87bf0f75ac6abd50f3807513db7814adba7d5a|False||List of data volume definitions for the task. See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html for the full list of available options.
user_code_launcher.config.mount_points|Array.Shape.c38382be9202f25e9131d79e298c3542bf5fbc3a|False||Mount points for data volumes in the main container of the task. See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html for more information.
user_code_launcher.config.server_sidecar_containers|Array.Permissive|False||Additional sidecar containers to include in code server task definitions.
user_code_launcher.config.run_sidecar_containers|Array.Permissive|False||Additional sidecar containers to include in run task definitions.
user_code_launcher.config.run_ecs_tags|Array.Shape.6c88bf764bc82039acb1e5b7542b223e7407c3bd|False||Additional tags to apply to the launched ECS task.
user_code_launcher.config.server_ecs_tags|Array.Shape.6c88bf764bc82039acb1e5b7542b223e7407c3bd|False||Additional tags to apply to the launched ECS task for a code server.
user_code_launcher.config.server_health_check|Permissive|False||Health check to include in code server task definitions.
user_code_launcher.config.server_ttl.full_deployments.enabled|BoolSourceType|True||Whether to shut down servers created by the agent for full deployments when they are not serving requests
user_code_launcher.config.server_ttl.full_deployments.ttl_seconds|IntSourceType|False|86400|If the `enabled` flag is set , how long to leave a server running for a once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.branch_deployments.ttl_seconds|IntSourceType|False|86400|How long to leave a server for a branch deployment running once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.max_servers|IntSourceType|False|25|In addition to the TTL, ensure that the maximum number of servers that are up at any given time and not currently serving requests stays below this number.
user_code_launcher.config.server_ttl.enabled|BoolSourceType|False||Deprecated - use `full_deployments.enabled` instead
user_code_launcher.config.server_ttl.ttl_seconds|IntSourceType|False||Deprecated - use `full_deployments.ttl_seconds` instead
user_code_launcher.config.defer_job_snapshots|BoolSourceType|False|True|Do not include full job snapshots in the workspace snapshot, upload them separately if they have not been previously uploaded.
user_code_launcher.config.upload_snapshots_on_startup|BoolSourceType|False|True|Upload information about code locations to Dagster Cloud whenever the agent starts up, even if the code location has not changed since the last upload.
user_code_launcher.config.requires_healthcheck|BoolSourceType|False|False|Whether the agent update process expects a readiness sentinel to be written before an agent is considered healthy. If using zero-downtime agent updates, this should be set to True.
</TabItem>
<TabItem value="docker" label="Docker">
|Config Path|Type|Required|Default|Description|
|--|--|--|--|--|
user_code_launcher.config.networks|Array.StringSourceType|False||Names of the networks to which to connect the launched container at creation time
user_code_launcher.config.env_vars|Array.String|False||The list of environment variables names to include in the docker container. Each can be of the form KEY=VALUE or just KEY (in which case the value will be pulled from the local environment)
user_code_launcher.config.container_kwargs|Permissive|False||key-value pairs that can be passed into containers.create. See https://docker-py.readthedocs.io/en/stable/containers.html for the full list of available options.
user_code_launcher.config.server_process_startup_timeout|IntSourceType|False|180|Timeout when waiting for a code server to be ready after it is created
user_code_launcher.config.server_ttl.full_deployments.enabled|BoolSourceType|True||Whether to shut down servers created by the agent for full deployments when they are not serving requests
user_code_launcher.config.server_ttl.full_deployments.ttl_seconds|IntSourceType|False|86400|If the `enabled` flag is set , how long to leave a server running for a once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.branch_deployments.ttl_seconds|IntSourceType|False|86400|How long to leave a server for a branch deployment running once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.max_servers|IntSourceType|False|25|In addition to the TTL, ensure that the maximum number of servers that are up at any given time and not currently serving requests stays below this number.
user_code_launcher.config.server_ttl.enabled|BoolSourceType|False||Deprecated - use `full_deployments.enabled` instead
user_code_launcher.config.server_ttl.ttl_seconds|IntSourceType|False||Deprecated - use `full_deployments.ttl_seconds` instead
user_code_launcher.config.defer_job_snapshots|BoolSourceType|False|True|Do not include full job snapshots in the workspace snapshot, upload them separately if they have not been previously uploaded.
user_code_launcher.config.upload_snapshots_on_startup|BoolSourceType|False|True|Upload information about code locations to Dagster Cloud whenever the agent starts up, even if the code location has not changed since the last upload.
user_code_launcher.config.requires_healthcheck|BoolSourceType|False|False|Whether the agent update process expects a readiness sentinel to be written before an agent is considered healthy. If using zero-downtime agent updates, this should be set to True.
</TabItem>
<TabItem value="process" label="In Process">
|Config Path|Type|Required|Default|Description|
|--|--|--|--|--|
user_code_launcher.config.server_process_startup_timeout|IntSourceType|False|180|Timeout when waiting for a code server to be ready after it is created
user_code_launcher.config.wait_for_processes|BoolSourceType|False|False|When cleaning up the agent, wait for any subprocesses to finish before shutting down. Generally only needed in tests/automation.
user_code_launcher.config.code_server_metrics.enabled|Bool|False|False|
user_code_launcher.config.agent_metrics.enabled|Bool|False|False|
user_code_launcher.config.server_ttl.full_deployments.enabled|BoolSourceType|True||Whether to shut down servers created by the agent for full deployments when they are not serving requests
user_code_launcher.config.server_ttl.full_deployments.ttl_seconds|IntSourceType|False|86400|If the `enabled` flag is set , how long to leave a server running for a once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.branch_deployments.ttl_seconds|IntSourceType|False|86400|How long to leave a server for a branch deployment running once it has been launched. Decreasing this value will cause fewer servers to be running at once, but request latency may increase if more requests need to wait for a server to launch
user_code_launcher.config.server_ttl.max_servers|IntSourceType|False|25|In addition to the TTL, ensure that the maximum number of servers that are up at any given time and not currently serving requests stays below this number.
user_code_launcher.config.server_ttl.enabled|BoolSourceType|False||Deprecated - use `full_deployments.enabled` instead
user_code_launcher.config.server_ttl.ttl_seconds|IntSourceType|False||Deprecated - use `full_deployments.ttl_seconds` instead
user_code_launcher.config.defer_job_snapshots|BoolSourceType|False|True|Do not include full job snapshots in the workspace snapshot, upload them separately if they have not been previously uploaded.
user_code_launcher.config.upload_snapshots_on_startup|BoolSourceType|False|True|Upload information about code locations to Dagster Cloud whenever the agent starts up, even if the code location has not changed since the last upload.
user_code_launcher.config.requires_healthcheck|BoolSourceType|False|False|Whether the agent update process expects a readiness sentinel to be written before an agent is considered healthy. If using zero-downtime agent updates, this should be set to True.
</TabItem>
</Tabs>
