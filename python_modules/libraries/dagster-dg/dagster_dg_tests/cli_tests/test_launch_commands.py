import inspect
import json
import subprocess
import textwrap
from pathlib import Path

import yaml
from dagster_dg.utils import ensure_dagster_dg_tests_import

ensure_dagster_dg_tests_import()
from dagster_dg.cli.utils import activate_venv

from dagster_dg_tests.utils import ProxyRunner, isolated_example_project_foo_bar


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


def test_launch_assets() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            python_environment="uv_managed",
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.components.DefsFolderComponent", "mydefs"],
                check=True,
            )

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
                f.write(defs_source)

            result = subprocess.run(
                ["dg", "launch", "--assets", "my_asset_1"],
                check=True,
                capture_output=True,
            )

            assert "Started execution of run for" in result.stderr.decode("utf-8")
            assert "RUN_SUCCESS" in result.stderr.decode("utf-8")

            result = subprocess.run(
                ["dg", "launch", "--assets", "my_asset_2", "--partition", "2024-02-03"],
                check=True,
                capture_output=True,
            )

            assert "Started execution of run for" in result.stderr.decode("utf-8")
            assert "Materialized value my_asset_2" in result.stderr.decode("utf-8")
            assert "2024-02-03" in result.stderr.decode("utf-8")

            result = subprocess.run(
                [
                    "dg",
                    "launch",
                    "--assets",
                    "my_asset_2",
                    "--partition-range",
                    "2024-02-03...2024-02-03",
                ],
                check=True,
                capture_output=True,
            )

            assert "Started execution of run for" in result.stderr.decode("utf-8")
            assert "Materialized value my_asset_2" in result.stderr.decode("utf-8")

            assert "2024-02-03" in result.stderr.decode("utf-8")

            result = subprocess.run(
                [
                    "dg",
                    "launch",
                    "--assets",
                    "my_asset_3",
                    "--config-json",
                    '{"ops": {"my_asset_3": {"config": {"foo": 7 } } } }',
                ],
                check=False,
                capture_output=True,
            )

            assert "CONFIG: 7" in result.stderr.decode("utf-8")

            result = subprocess.run(
                [
                    "dg",
                    "launch",
                    "--assets",
                    "nonexistant",
                ],
                check=False,
                capture_output=True,
            )
            assert result.returncode != 0

            assert "no AssetsDefinition objects supply these keys" in result.stderr.decode("utf-8")


def test_launch_assets_config_files(capfd) -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            python_environment="uv_managed",
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
    ):
        result = subprocess.run(
            ["dg", "scaffold", "defs", "dagster.components.DefsFolderComponent", "mydefs"],
            check=True,
        )
        assert result.returncode == 0

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
            f.write(defs_source)

        Path("config.json").write_text(json.dumps({"ops": {"my_asset_3": {"config": {"foo": 7}}}}))

        result = subprocess.run(
            ["dg", "launch", "--assets", "my_asset_3", "--config", "config.json"], check=True
        )
        assert result.returncode == 0

        captured = capfd.readouterr()
        assert "CONFIG: 7" in captured.err

        Path("config.yaml").write_text(yaml.dump({"ops": {"my_asset_3": {"config": {"foo": 3}}}}))
        result = subprocess.run(
            ["dg", "launch", "--assets", "my_asset_3", "-c", "config.yaml"], check=True
        )
        assert result.returncode == 0

        captured = capfd.readouterr()
        assert "CONFIG: 3" in captured.err

        Path("config.yaml").write_text(yaml.dump({"ops": {"my_asset_3": {"config": {"foo": 3}}}}))
        result = subprocess.run(
            ["dg", "launch", "--assets", "my_asset_3", "-c", "config.yaml", "-c", "config.json"],
            check=True,
        )
        assert result.returncode == 0

        captured = capfd.readouterr()
        assert "CONFIG: 7" in captured.err
