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


def test_run_task_retryrable_failure(ecs, instance, workspace, run, other_run, monkeypatch):
    original = ecs.run_task

    out_of_capacity_response = {
        "tasks": [],
        "failures": [
            {
                "arn": "missing-capacity",
                "reason": "Capacity is unavailable at this time. Please try again later or in a different availability zone",
                "detail": "boom",
            },
        ],
    }

    retryable_failures = iter([out_of_capacity_response])

    def run_task(*args, **kwargs):
        try:
            return next(retryable_failures)
        except StopIteration:
            return original(*args, **kwargs)

    instance.run_launcher.ecs.run_task = run_task

    instance.launch_run(run.run_id, workspace)

    # reset our mock and test again with 0 retries
    retryable_failures = iter([out_of_capacity_response])

    monkeypatch.setenv("RUN_TASK_RETRIES", "0")

    with pytest.raises(Exception) as ex:
        instance.launch_run(other_run.run_id, workspace)

    assert ex.match("Capacity is unavailable")
