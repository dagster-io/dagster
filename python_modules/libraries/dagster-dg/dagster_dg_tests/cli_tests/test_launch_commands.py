import inspect
import textwrap
from pathlib import Path

from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()

from dagster_dg_tests.utils import (
    ProxyRunner,
    assert_runner_result,
    isolated_example_project_foo_bar,
)


def _sample_defs():
    from dagster import DailyPartitionsDefinition, asset, schedule, sensor

    @asset
    def my_asset_1(): ...

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"),
    )
    def my_asset_2(): ...

    @asset(config_schema={"foo": int})
    def my_asset_3(context):
        context.log.info(f"CONFIG: {context.op_config['foo']}")

    @schedule(cron_schedule="@daily", target=[my_asset_1])
    def my_schedule(): ...

    @sensor(target=[my_asset_2])
    def my_sensor(): ...


def test_launch_assets(capfd) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(runner, in_workspace=False),
    ):
        result = runner.invoke("scaffold", "dagster.components.DefsFolderComponent", "mydefs")
        assert_runner_result(result)

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
            f.write(defs_source)

        result = runner.invoke("launch", "--assets", "my_asset_1")
        assert_runner_result(result)

        captured = capfd.readouterr()
        print(str(captured.err))  # noqa

        assert "Started execution of run for" in captured.err
        assert "RUN_SUCCESS" in captured.err

        result = runner.invoke("launch", "--assets", "my_asset_2", "--partition", "2024-02-03")
        assert_runner_result(result)

        captured = capfd.readouterr()
        print(str(captured.err))  # noqa
        assert "Started execution of run for" in captured.err
        assert "Materialized value my_asset_2" in captured.err

        result = runner.invoke(
            "launch",
            "--assets",
            "my_asset_2",
            "--partition-range",
            "2024-02-03...2024-02-03",
        )
        assert_runner_result(result)

        captured = capfd.readouterr()
        print(str(captured.err))  # noqa
        assert "Started execution of run for" in captured.err
        assert "Materialized value my_asset_2" in captured.err

        assert "2024-02-03" in captured.err

        result = runner.invoke(
            "launch",
            "--assets",
            "my_asset_3",
            "--config-json",
            '{"ops": {"my_asset_3": {"config": {"foo": 7 } } } }',
        )
        assert_runner_result(result)

        captured = capfd.readouterr()
        print(str(captured.err))  # noqa
        assert "CONFIG: 7" in captured.err

        result = runner.invoke(
            "launch",
            "--assets",
            "nonexistant",
        )
        assert_runner_result(result, exit_0=False)
        captured = capfd.readouterr()
        print(str(captured.err))  # noqa
        assert "no AssetsDefinition objects supply these keys" in captured.err
        assert "Failed to launch assets." in result.output
