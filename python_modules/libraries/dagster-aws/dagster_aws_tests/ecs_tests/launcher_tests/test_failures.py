import pytest


def test_run_task_failure(ecs, instance, workspace, run):
    def run_task(self=ecs, **kwargs):
        self.stubber.activate()
        self.stubber.add_response(
            method="run_task",
            service_response={
                "tasks": [],
                "failures": [
                    {"arn": "failing-arn-1", "reason": "boom", "detail": "detailed boom 1"},
                    {"arn": "failing-arn-2", "reason": "boom", "detail": "detailed boom 2"},
                ],
            },
            expected_params={**kwargs},
        )
        response = self.client.run_task(**kwargs)
        self.stubber.deactivate()
        return response

    instance.run_launcher.ecs.run_task = run_task

    with pytest.raises(Exception) as ex:
        instance.launch_run(run.run_id, workspace)

    assert ex.match("Task failing-arn-1 failed because boom: detailed boom 1")
    assert ex.match("Task failing-arn-2 failed because boom: detailed boom 2")
