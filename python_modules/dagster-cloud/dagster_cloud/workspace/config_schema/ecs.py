from dagster import Array, BoolSource, Field, Noneable, Permissive, Shape, StringSource

# Shared between user code launcher config and container context
SHARED_ECS_CONFIG = {
    "server_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description="The CPU override to use for the launched task.",
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description="The memory override to use for the launched task.",
                ),
                "ephemeral_storage": Field(
                    int,
                    is_required=False,
                    description="The ephemeral storage, in GiB, to use for the launched task.",
                ),
            }
        )
    ),
    "run_resources": Field(
        Permissive(
            {
                "cpu": Field(
                    str,
                    is_required=False,
                    description="The CPU override to use for the launched task.",
                ),
                "memory": Field(
                    str,
                    is_required=False,
                    description="The memory override to use for the launched task.",
                ),
                "ephemeral_storage": Field(
                    int,
                    is_required=False,
                    description="The ephemeral storage, in GiB, to use for the launched task.",
                ),
            }
        )
    ),
    "runtime_platform": Field(
        Shape(
            {
                "cpuArchitecture": Field(StringSource, is_required=False),
                "operatingSystemFamily": Field(StringSource, is_required=False),
            }
        ),
        is_required=False,
        description=(
            "The operating system that the task definition is running on. See"
            " https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ecs.html#ECS.Client.register_task_definition"
            " for the available options."
        ),
    ),
    "volumes": Field(
        Array(
            Permissive(
                {
                    "name": Field(StringSource, is_required=False),
                }
            )
        ),
        is_required=False,
        description=(
            "List of data volume definitions for the task. See"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html"
            " for the full list of available options."
        ),
    ),
    "mount_points": Field(
        Array(
            Shape(
                {
                    "sourceVolume": Field(StringSource, is_required=False),
                    "containerPath": Field(StringSource, is_required=False),
                    "readOnly": Field(BoolSource, is_required=False),
                }
            )
        ),
        is_required=False,
        description=(
            "Mount points for data volumes in the main container of the task."
            " See https://docs.aws.amazon.com/AmazonECS/latest/developerguide/efs-volumes.html"
            " for more information."
        ),
    ),
    "server_sidecar_containers": Field(
        Array(Permissive({})),
        is_required=False,
        description="Additional sidecar containers to include in code server task definitions.",
    ),
    "run_sidecar_containers": Field(
        Array(Permissive({})),
        is_required=False,
        description="Additional sidecar containers to include in run task definitions.",
    ),
    "run_ecs_tags": Field(
        Array(
            {
                "key": Field(StringSource, is_required=True),
                "value": Field(StringSource, is_required=False),
            }
        ),
        is_required=False,
        description="Additional tags to apply to the launched ECS task.",
    ),
    "server_ecs_tags": Field(
        Array(
            {
                "key": Field(StringSource, is_required=True),
                "value": Field(StringSource, is_required=False),
            }
        ),
        is_required=False,
        description="Additional tags to apply to the launched ECS task for a code server.",
    ),
    "server_health_check": Field(
        Permissive(),
        is_required=False,
        description="Health check to include in code server task definitions.",
    ),
    "repository_credentials": Field(
        StringSource,
        is_required=False,
        description=(
            "The arn of the secret to authenticate into your private container registry."
            " This does not apply if you are leveraging ECR for your images, see"
            " https://docs.aws.amazon.com/AmazonECS/latest/userguide/private-auth.html."
        ),
    ),
}


ECS_CONTAINER_CONTEXT_CONFIG = {
    "secrets": Field(
        Noneable(Array(Shape({"name": StringSource, "valueFrom": StringSource}))),
        is_required=False,
        description=(
            "An array of AWS Secrets Manager secrets. These secrets will "
            "be mounted as environment variables in the container. See "
            "https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_Secret.html."
        ),
    ),
    "secrets_tags": Field(
        Noneable(Array(StringSource)),
        is_required=False,
        description=(
            "AWS Secrets Manager secrets with these tags will be mounted as "
            "environment variables in the container."
        ),
    ),
    "env_vars": Field(
        [StringSource],
        is_required=False,
        description=(
            "List of environment variable names to include in the ECS task. "
            "Each can be of the form KEY=VALUE or just KEY (in which case the value will be pulled "
            "from the current process)"
        ),
    ),
    "task_role_arn": Field(
        StringSource,
        is_required=False,
        description=(
            "ARN of the IAM role for launched tasks. See"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html. "
        ),
    ),
    "execution_role_arn": Field(
        StringSource,
        is_required=False,
        description=(
            "ARN of the task execution role for the ECS container and Fargate agent to make AWS API"
            " calls on your behalf. See"
            " https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html. "
        ),
    ),
    **SHARED_ECS_CONFIG,
}
