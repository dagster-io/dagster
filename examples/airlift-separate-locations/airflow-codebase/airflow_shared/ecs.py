from airflow.models.operator import BaseOperator


class EcsRunTaskOperator(BaseOperator):
    # Fake version of the ecs run operator
    def __init__(self, cluster_name: str, task_definition: dict, overrides: dict, *args, **kwargs):
        self._overrides = overrides
        self._cluster_name = cluster_name
        self._task_definition = task_definition
        super().__init__(*args, **kwargs)

    def execute(self, context) -> None:
        # we're not actually going to execute the task definition here
        ...
