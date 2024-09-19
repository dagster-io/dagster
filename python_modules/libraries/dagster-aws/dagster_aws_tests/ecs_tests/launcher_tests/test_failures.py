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
                    {"arn": "missing-detail", "reason": "too succinct"},
                    {"reason": "ran out of arns"},
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

    assert ex.match(
        "Task failing-arn-1 failed. Failure reason: boom Failure details: detailed boom 1\n"
    )
    assert ex.match("\nTask missing-detail failed. Failure reason: too succinct\n")
    assert ex.match("Task failed. Failure reason: ran out of arns")
