from types import SimpleNamespace

import dagster_celery_docker.executor as celery_docker_executor


def test_container_kwargs_environment_values_can_contain_equals(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        celery_docker_executor,
        "unpack_value",
        lambda _packed, as_type: SimpleNamespace(
            instance_ref="ref",
            run_id="run-id",
            step_keys_to_execute=["step"],
            get_command_args=lambda: ["dagster", "api", "execute_step"],
        ),
    )
    monkeypatch.setattr(celery_docker_executor, "serialize_value", lambda value: value)
    monkeypatch.setattr(celery_docker_executor, "filter_dagster_events_from_cli_logs", lambda _: [])
    monkeypatch.setattr(
        celery_docker_executor,
        "DagsterInstance",
        SimpleNamespace(
            from_ref=lambda _ref: SimpleNamespace(
                get_run_by_id=lambda _run_id: SimpleNamespace(),
                report_engine_event=lambda *_args, **_kwargs: "engine-event",
            )
        ),
    )

    def fake_run(*_args, **kwargs):
        captured["environment"] = kwargs["environment"]
        return b""

    monkeypatch.setattr(
        celery_docker_executor.docker.client,
        "from_env",
        lambda: SimpleNamespace(containers=SimpleNamespace(run=fake_run)),
    )

    class FakeCeleryApp:
        def task(self, **_kwargs):
            return lambda fn: fn

    task = celery_docker_executor.create_docker_task(FakeCeleryApp())
    task(
        SimpleNamespace(request=SimpleNamespace(hostname="worker")),
        {},
        {"image": "busybox", "container_kwargs": {"environment": ["TOKEN=a=b"]}},
    )

    assert captured["environment"]["TOKEN"] == "a=b"
