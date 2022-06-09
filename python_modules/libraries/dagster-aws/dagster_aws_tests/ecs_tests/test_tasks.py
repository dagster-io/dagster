from dagster_aws.ecs.tasks import dagster_task_definition_dict


def test_create_dagster_task_definition_dict():
    task_def_dict = dagster_task_definition_dict(
        "my_task",
        "foo_image:bar",
        ["dagster", "api", "execute_run"],
        execution_role_arn="fake-role",
        region_name="us_east_=",
        task_role_arn="fake-task-role",
        env={
            "FOO_ENV_VAR": "BAR_VALUE",
        },
        secrets={
            "FOO_SECRET": "BAR_SECRET_VALUE",
        },
        log_group="my-log-group",
    )

    assert task_def_dict == {
        "family": "my_task",
        "requiresCompatibilities": ["FARGATE"],
        "networkMode": "awsvpc",
        "containerDefinitions": [
            {
                "name": "my_task",
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
