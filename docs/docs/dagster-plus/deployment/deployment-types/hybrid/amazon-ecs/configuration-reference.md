---
description: Dagster+ configuration reference for Amazon ECS agents.
sidebar_position: 400
title: Configuration reference
---

:::note

This guide is applicable to Dagster+.

:::

This reference describes the various configuration options Dagster+ currently supports for [Amazon ECS agents](/dagster-plus/deployment/deployment-types/hybrid/amazon-ecs).

## Per-location configuration

When [adding a code location](/dagster-plus/deployment/code-locations/) to Dagster+ with an Amazon ECS agent, you can use the `container_context` key on the location configuration to add additional ECS-specific configuration that will be applied to any ECS tasks associated with that code location.

**Note**: If you're using the Dagster+ Github action, the `container_context` key can also be set for each location in your `dagster_cloud.yaml` file.

The following example [`dagster_cloud.yaml`](/dagster-plus/deployment/code-locations/dagster-cloud-yaml) file illustrates the available fields:

```yaml
locations:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      ecs:
        env_vars:
          - DATABASE_NAME=staging
          - DATABASE_PASSWORD
        secrets:
          - name: 'MY_API_TOKEN'
            valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::'
          - name: 'MY_PASSWORD'
            valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:password::'
        secrets_tags:
          - 'my_tag_name'
        server_resources: # Resources for code servers launched by the agent for this location
          cpu: 256
          memory: 512
          replica_count: 1
        run_resources: # Resources for runs launched by the agent for this location
          cpu: 4096
          memory: 16384
        execution_role_arn: arn:aws:iam::123456789012:role/MyECSExecutionRole
        task_role_arn: arn:aws:iam::123456789012:role/MyECSTaskRole
        mount_points:
          - sourceVolume: myEfsVolume
            containerPath: '/mount/efs'
            readOnly: True
        volumes:
          - name: myEfsVolume
            efsVolumeConfiguration:
              fileSystemId: fs-1234
              rootDirectory: /path/to/my/data
        server_sidecar_containers:
          - name: DatadogAgent
            image: public.ecr.aws/datadog/agent:latest
            environment:
              - name: ECS_FARGATE
                value: true
        run_sidecar_containers:
          - name: DatadogAgent
            image: public.ecr.aws/datadog/agent:latest
            environment:
              - name: ECS_FARGATE
                value: true
        server_ecs_tags:
          - key: MyEcsTagKey
            value: MyEcsTagValue
        run_ecs_tags:
          - key: MyEcsTagKeyWithoutValue
        repository_credentials: MyRepositoryCredentialsSecretArn
```

### Environment variables and secrets

Using the `container_context.ecs.env_vars` and `container_context.ecs.secrets` properties, you can configure environment variables and secrets for a specific code location.

```yaml
# dagster_cloud.yaml

locations:
  - location_name: cloud-examples
    image: dagster/dagster-cloud-examples:latest
    code_source:
      package_name: dagster_cloud_examples
    container_context:
      ecs:
        env_vars:
          - DATABASE_NAME=testing
          - DATABASE_PASSWORD
        secrets:
          - name: 'MY_API_TOKEN'
            valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:token::'
          - name: 'MY_PASSWORD'
            valueFrom: 'arn:aws:secretsmanager:us-east-1:123456789012:secret:FOO-AbCdEf:password::'
        secrets_tags:
          - 'my_tag_name'
```

| Property                           | Description                                                                                                                                                                                                                                                                                                 |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| container_context.ecs.env_vars     | A list of keys or key-value pairs for task inclusion. If value unspecified, pulls from agent task. Example: `FOO_ENV_VAR` set to `foo_value`, `BAR_ENV_VAR` set to agent task value.                                                                                                                        |
| container_context.ecs.secrets      | Individual secrets specified using the [same structure as the ECS API.](https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Secret.html)                                                                                                                                                          |
| container_context.ecs.secrets_tags | A list of tag names. Each secret tagged with any of those tag names in AWS Secrets Manager will be included in the launched tasks as environment variables. The name of the environment variable will be the name of the secret, and the value of the environment variable will be the value of the secret. |

Refer to the following guides for more info about environment variables:

- [Dagster+ environment variables and secrets](/dagster-plus/deployment/management/environment-variables/)
- [Using environment variables and secrets in Dagster code](/guides/deploy/using-environment-variables-and-secrets)

## Per-job configuration: Resource limits

You can use job tags to customize the CPU and memory of every run for that job:

```python
from dagster import job, op

@op()
def my_op(context):
  context.log.info('running')

@job(
  tags = {
    "ecs/cpu": "256",
    "ecs/memory": "512",
  }
)
def my_job():
  my_op()
```

[Fargate tasks only support certain combinations of CPU and memory.](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html)

If the `ecs/cpu` or `ecs/memory` tags are set, they will override any defaults set on the code location or the deployment.

## Per-deployment configuration

This section describes the properties of the `dagster.yaml` configuration file used by Amazon ECS agents. Typically, this file is created by the CloudFormation template that deploys the agent and can be found within the agent task definition's command.

To change these properties, edit the CloudFormation template and redeploy the CloudFormation stack.

```yaml
instance_class:
  module: dagster_cloud
  class: DagsterCloudAgentInstance

dagster_cloud_api:
  agent_token: <Agent Token String>
  deployments:
    - <Deployment Name>
    - <Optional Additional Deployment Name>
  branch_deployments: <true|false>

user_code_launcher:
  module: dagster_cloud.workspace.ecs
  class: EcsUserCodeLauncher
  config:
    cluster: <Cluster Name>
    subnets:
      - <Subnet Id 1>
      - <Subnet Id 2>
    security_group_ids:
      - <Security Group ID>
    service_discovery_namespace_id: <Service Discovery Namespace Id>
    execution_role_arn: <Task Execution Role Arn>
    task_role_arn: <Task Role Arn>
    log_group: <Log Group Name>
    launch_type: <"FARGATE"|"EC2">
    server_process_startup_timeout: <Timeout in seconds>
    server_resources:
      cpu: <CPU value>
      memory: <Memory value>
    server_sidecar_containers:
      - name: SidecarName
        image: SidecarImage
        <Additional container fields>
    run_resources:
      cpu: <CPU value>
      memory: <Memory value>
    run_sidecar_containers:
      - name: SidecarName
        image: SidecarImage
        <Additional container fields>
    mount_points:
      - <List of mountPoints to pass into register_task_definition>
    volumes:
      - <List of volumes to pass into register_task_definition>
    server_ecs_tags:
      - key: MyEcsTagKey
        value: MyEcsTagValue
    run_ecs_tags:
      - key: MyEcsTagKeyWithoutValue
    repository_credentials: MyRepositoryCredentialsSecretArn

isolated_agents:
  enabled: <true|false>
agent_queues:
  include_default_queue: <true|false>
  additional_queues:
    - <queue name>
    - <additional queue name>
```

### dagster_cloud_api properties

| Property                             | Description                                             |
| ------------------------------------ | ------------------------------------------------------- |
| dagster_cloud_api.agent_token        | An agent token for the agent to use for authentication. |
| dagster_cloud_api.deployments        | The names of full deployments for the agent to serve.   |
| dagster_cloud_api.branch_deployments | Whether the agent should serve all branch deployments.  |

### user_code_launcher properties

| Property                              | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| config.cluster                        | Name of ECS cluster with Fargate or EC2 capacity provider                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| config.launch_type                    | ECS launch type: <br/>• `FARGATE`<br/>• `EC2` **Note:** Using this launch type requires you to have an EC2 capacity provider installed and additional operational overhead to run the agent.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| config.subnets                        | **At least one subnet is required**. Dagster+ tasks require a route to the internet so they can access our API server. How this requirement is satisfied depends on the type of subnet provided: <br/>• **Public subnets** - The ECS agent will assign each task a public IP address. Note that [ECS tasks on EC2](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-networking-awsvpc.html) launched within public subnets do not have access to the internet, so a public subnet will only work for Fargate tasks. <br/>•**Private subnets** - The ECS agent assumes you've configured a NAT gateway with an attached NAT gateway. Tasks will **not** be assigned a public IP address. |
| config.security_group_ids             | A list of [security groups](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-securitygroup.html) to use for tasks launched by the agent.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| config.service_discovery_namespace_id | The name of a [private DNS namespace](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-servicediscovery-privatednsnamespace.html).<br/>The ECS agent launches each code location as its own ECS service. The agent communicates with these services via [AWS CloudMap service discovery.](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-discovery.html)                                                                                                                                                                                                                                                                                                |
| config.execution_role_arn             | The ARN of the [Amazon ECS task execution IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html). This role allows ECS to interact with AWS resources on your behalf, such as getting an image from ECR or pushing logs to CloudWatch. <br/>**Note**:This role must include a trust relationship that allows ECS to use it.                                                                                                                                                                                                                                                                                                                                |
| config.task_role_arn                  | The ARN of the [Amazon ECS task IAM role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html). This role allows the containers running in the ECS task to interact with AWS. <br/> **Note**: This role must include a trust relationship that allows ECS to use it.                                                                                                                                                                                                                                                                                                                                                                                                        |
| config.log_group                      | The name of a CloudWatch [log group](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html#Create-Log-Group).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| config.server_process_startup_timeout | The amount of time, in seconds, to wait for code to import when launching a new service for a code location. If your code takes an unusually long time to load after your ECS task starts up and results in timeouts in the **Deployment** tab, you can increase this setting above the default. **Note** This setting isn't applicable to the time it takes for a job to execute. <br/>• **Default** - 180 (seconds)                                                                                                                                                                                                                                                                                   |
| config.ecs_timeout                    | How long (in seconds) to wait for ECS to spin up a new service and task for a code server. If your ECS tasks take an unusually long time to start and result in timeouts, you can increase this setting above the default. <br/>• **Default** - 300 (seconds)                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| config.ecs_grace_period               | How long (in seconds) to continue polling if an ECS API endpoint fails during creation of a new code server (because the ECS API is eventually consistent). <br/>• **Default** - 30 (seconds)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| config.server_resources               | The resources that the agent should allocate to the ECS service for each code location that it creates. If set, must be a dictionary with a `cpu` and/or `memory` key. **Note**: [Fargate tasks only support certain combinations of CPU and memory.](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html)                                                                                                                                                                                                                                                                                                                                                           |
| config.server_sidecar_containers      | Additional sidecar containers to include along with the Dagster container. If set, must be a list of dictionaries with valid ECS container definitions.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| config.run_resources                  | The resources that the agent should allocate to the ECS task that it creates for each run. If set, must be a dictionary with a `cpu` and/or `memory` key. **Note**: [Fargate tasks only support certain combinations of CPU and memory.](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-cpu-memory-error.html)                                                                                                                                                                                                                                                                                                                                                                        |
| config.run_sidecar_containers         | Additional sidecar containers to include along with the Dagster container. If set, must be a list of dictionaries with valid ECS container definitions.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| config.mount_points                   | Mount points to include in the Dagster container. If set, should be a list of dictionaries matching the `mountPoints` field when specifying a container definition to boto3.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| config.volumes                        | Additional volumes to include in the task definition. If set, should be a list of dictionaries matching the volumes argument to `register_task_definition` in boto3.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| config.server_ecs_tags                | Additional ECS tags to include in the service for each code location. If set, must be a list of dictionaries, each with a `key` key and optional `value` key.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| config.run_ecs_tags                   | AAdditional ECS tags to include in the task for each run. If set, must be a list of dictionaries, each with a `key` key and optional `value` key.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| config.repository_credentials         | Optional arn of the secret to authenticate into your private container registry. This does not apply if you are leveraging ECR for your images, see the [AWS private auth guide.](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/private-auth.html)                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| config.enable_ecs_exec                | Boolean that determines whether tasks created by the agent should be configured with the needed linuxParameters and permissions to use [ECS Exec](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs-exec.html) to shell into the task. Also grants the `SYS_PTRACE` linux capability to enable running tools like py-spy to debug slow or hanging tasks. Defaults to false. **Note**: For ECS Exec to work, the task IAM role must be granted [certain permissions](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html#ecs-exec-required-iam-permissions).                                                                                                   |

### isolated_agents properties

| Property                | Description                                                                                                                                                                                                       |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| isolated_agents.enabled | When enabled, agents are isolated and will not be able to access each others' resources. See the [Running multiple agents guide](/dagster-plus/deployment/deployment-types/hybrid/multiple) for more information. |

### agent_queues properties

These settings specify the queue(s) the agent will obtain requests from. See [Routing requests to specific agents](/dagster-plus/deployment/deployment-types/hybrid/multiple).

| Property                           | Description                                          |
| ---------------------------------- | ---------------------------------------------------- |
| agent_queues.include_default_queue | If true, agent processes requests from default queue |
| agent_queues.additional_queues     | List of additional queues for agent processing       |
