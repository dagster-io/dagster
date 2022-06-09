from dagster_aws.ecs.tasks import DagsterEcsTaskConfig


def test_create_dagster_task_definition_dict():
    task_config = DagsterEcsTaskConfig(
        family="my_task",
        container_name="run",
        cluster="my-ecs-cluster",
        image="foo_image:bar",
        command=["dagster", "api", "execute_run"],
        execution_role_arn="fake-role",
        log_configuration={
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "my-log-group",
                "awslogs-region": "us_east_=",
                "awslogs-stream-prefix": "my_task",
            },
        },
        task_role_arn="fake-task-role",
        environment=[
            {
                "name": "FOO_ENV_VAR",
                "value": "BAR_VALUE",
            }
        ],
        secrets=[
            {
                "name": "FOO_SECRET",
                "valueFrom": "BAR_SECRET_VALUE",
            }
        ],
        subnets=["SUBNET1", "SUBNET2"],
        security_groups=["security-group-1", "security-group-2"],
        assign_public_ip=False,
    )

    assert task_config.task_definition() == {
        "family": "my_task",
        "requiresCompatibilities": ["FARGATE"],
        "networkMode": "awsvpc",
        "containerDefinitions": [
            {
                "name": "run",
                "image": "foo_image:bar",
                "environment": [{"name": "FOO_ENV_VAR", "value": "BAR_VALUE"}],
                "command": ["dagster", "api", "execute_run"],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": "my-log-group",
                        "awslogs-region": "us_east_=",
                        "awslogs-stream-prefix": "my_task",
                    },
                },
                "secrets": [{"name": "FOO_SECRET", "valueFrom": "BAR_SECRET_VALUE"}],
            }
        ],
        "executionRoleArn": "fake-role",
        "cpu": "256",
        "memory": "512",
        "taskRoleArn": "fake-task-role",
    }
