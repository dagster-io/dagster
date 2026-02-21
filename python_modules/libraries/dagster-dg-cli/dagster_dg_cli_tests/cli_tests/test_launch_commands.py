import inspect
import json
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml
from dagster_dg_core.utils import activate_venv
from dagster_test.dg_utils.utils import ProxyRunner, isolated_example_project_foo_bar


def _sample_defs():
    from dagster import BackfillPolicy, DailyPartitionsDefinition, asset, schedule, sensor

    @asset
    def my_asset_1(): ...

    @asset(
        partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"),
        backfill_policy=BackfillPolicy.single_run(),
    )
    def my_asset_2(): ...

    @asset(config_schema={"foo": int})
    def my_asset_3(context):
        context.log.info(f"CONFIG: {context.op_config['foo']}")

    @schedule(cron_schedule="@daily", target=[my_asset_1])
    def my_schedule(): ...

    @sensor(target=[my_asset_2])
    def my_sensor(): ...


def _sample_job():
    from dagster import Config, DailyPartitionsDefinition, OpExecutionContext, job, op

    @op
    def my_op(context: OpExecutionContext):
        if context.has_partitions:
            context.log.info(
                f"PARTITION: {context.partition_key_range.start}...{context.partition_key_range.end}"
            )
        else:
            context.log.info("NO PARTITION")

    @op
    def my_other_op(context: OpExecutionContext):
        pass

    @job(partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"))
    def my_partitioned_job():
        my_op()
        my_other_op()

    class MyOpConfig(Config):
        foo: int

    @op
    def my_configured_op(context: OpExecutionContext, config: MyOpConfig):
        context.log.info(f"CONFIG: {config.foo}")

    @job()
    def my_configured_job():
        my_configured_op()


def _sample_single_job():
    from dagster import job, op

    @op
    def my_op():
        pass

    @job()
    def my_job():
        my_op()


def test_launch_assets() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
                f.write(defs_source)

            result = subprocess.run(
                ["dg", "launch", "--assets", "my_asset_1"],
                check=False,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0, result.stderr
            assert "Started execution of run for" in result.stderr
            assert "RUN_SUCCESS" in result.stderr

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


def test_launch_assets_config_files() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
    ):
        result = subprocess.run(
            ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
            check=True,
        )
        assert result.returncode == 0

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
            f.write(defs_source)

        Path("config.json").write_text(json.dumps({"ops": {"my_asset_3": {"config": {"foo": 7}}}}))

        result = subprocess.run(
            ["dg", "launch", "--assets", "my_asset_3", "--config", "config.json"],
            check=True,
            capture_output=True,
        )
        assert result.returncode == 0

        assert "CONFIG: 7" in result.stderr.decode("utf-8")

        Path("config.yaml").write_text(yaml.dump({"ops": {"my_asset_3": {"config": {"foo": 3}}}}))
        result = subprocess.run(
            ["dg", "launch", "--assets", "my_asset_3", "-c", "config.yaml"],
            check=True,
            capture_output=True,
        )
        assert result.returncode == 0

        assert "CONFIG: 3" in result.stderr.decode("utf-8")

        Path("config.yaml").write_text(yaml.dump({"ops": {"my_asset_3": {"config": {"foo": 3}}}}))
        result = subprocess.run(
            ["dg", "launch", "--assets", "my_asset_3", "-c", "config.yaml", "-c", "config.json"],
            check=True,
            capture_output=True,
        )
        assert result.returncode == 0

        assert "CONFIG: 7" in result.stderr.decode("utf-8")


def test_launch_job_partitioned() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(inspect.getsource(_sample_job).split("\n", 1)[1])
                f.write(defs_source)

            result = subprocess.run(
                ["dg", "launch", "--job", "my_partitioned_job"],
                check=True,
                capture_output=True,
            )

            assert "Started execution of run for" in result.stderr.decode("utf-8")
            assert "RUN_SUCCESS" in result.stderr.decode("utf-8")
            assert "NO PARTITION" in result.stderr.decode("utf-8")

            result = subprocess.run(
                ["dg", "launch", "--job", "my_partitioned_job", "--partition", "2024-01-01"],
                check=True,
                capture_output=True,
            )

            assert "Started execution of run for" in result.stderr.decode("utf-8")
            assert "RUN_SUCCESS" in result.stderr.decode("utf-8")
            assert "PARTITION: 2024-01-01...2024-01-01" in result.stderr.decode("utf-8")

            result = subprocess.run(
                [
                    "dg",
                    "launch",
                    "--job",
                    "my_partitioned_job",
                    "--partition-range",
                    "2024-01-01...2024-01-05",
                ],
                check=True,
                capture_output=True,
            )

            assert "Started execution of run for" in result.stderr.decode("utf-8")
            assert "RUN_SUCCESS" in result.stderr.decode("utf-8")
            assert "PARTITION: 2024-01-01...2024-01-05" in result.stderr.decode("utf-8")


def test_launch_job_configured() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
        ) as project_dir,
    ):
        with activate_venv(project_dir / ".venv"):
            subprocess.run(
                ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
                check=True,
            )

            with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
                defs_source = textwrap.dedent(inspect.getsource(_sample_job).split("\n", 1)[1])
                f.write(defs_source)

            with pytest.raises(subprocess.CalledProcessError):
                result = subprocess.run(
                    ["dg", "launch", "--job", "my_configured_job"],
                    check=True,
                    capture_output=True,
                )

            result = subprocess.run(
                [
                    "dg",
                    "launch",
                    "--job",
                    "my_configured_job",
                    "--config-json",
                    '{"ops": {"my_configured_op": {"config": {"foo": 7}}}}',
                ],
                check=True,
                capture_output=True,
            )

            assert "Started execution of run for" in result.stderr.decode("utf-8")
            assert "CONFIG: 7" in result.stderr.decode("utf-8")


def test_launch_job_config_files() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
    ):
        result = subprocess.run(
            ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
            check=True,
            capture_output=True,
        )
        assert result.returncode == 0

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_job).split("\n", 1)[1])
            f.write(defs_source)

        Path("config.json").write_text(
            json.dumps({"ops": {"my_configured_op": {"config": {"foo": 7}}}})
        )

        result = subprocess.run(
            ["dg", "launch", "--job", "my_configured_job", "--config", "config.json"],
            check=True,
            capture_output=True,
        )
        assert result.returncode == 0

        assert "CONFIG: 7" in result.stderr.decode("utf-8")

        Path("config.yaml").write_text(
            yaml.dump({"ops": {"my_configured_op": {"config": {"foo": 3}}}})
        )
        result = subprocess.run(
            ["dg", "launch", "--job", "my_configured_job", "-c", "config.yaml"],
            check=True,
            capture_output=True,
        )
        assert result.returncode == 0

        assert "CONFIG: 3" in result.stderr.decode("utf-8")

        Path("config.yaml").write_text(
            yaml.dump({"ops": {"my_configured_op": {"config": {"foo": 3}}}})
        )
        result = subprocess.run(
            [
                "dg",
                "launch",
                "--job",
                "my_configured_job",
                "-c",
                "config.yaml",
                "-c",
                "config.json",
            ],
            check=True,
            capture_output=True,
        )
        assert result.returncode == 0

        assert "CONFIG: 7" in result.stderr.decode("utf-8")


def test_launch_job_point_to_module_explicitly() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
    ):
        result = subprocess.run(
            ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
            check=True,
        )
        assert result.returncode == 0

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_single_job).split("\n", 1)[1])
            f.write(defs_source)

        result = subprocess.run(
            [
                "dg",
                "launch",
                "--module-name",
                "foo_bar.defs.mydefs.definitions",
                "--job",
                "my_job",
            ],
            check=True,
        )
        assert result.returncode == 0, result.stderr.decode("utf-8")


def test_launch_assets_point_to_module_explicitly() -> None:
    with (
        ProxyRunner.test() as runner,
        isolated_example_project_foo_bar(
            runner,
            in_workspace=False,
            uv_sync=True,
        ) as project_dir,
        activate_venv(project_dir / ".venv"),
    ):
        result = subprocess.run(
            ["dg", "scaffold", "defs", "dagster.DefsFolderComponent", "mydefs"],
            check=True,
        )
        assert result.returncode == 0

        with Path("src/foo_bar/defs/mydefs/definitions.py").open("w") as f:
            defs_source = textwrap.dedent(inspect.getsource(_sample_defs).split("\n", 1)[1])
            f.write(defs_source)

        result = subprocess.run(
            [
                "dg",
                "launch",
                "--module-name",
                "foo_bar.defs.mydefs.definitions",
                "--assets",
                "my_asset_1",
            ],
            check=True,
        )
        assert result.returncode == 0, result.stderr.decode("utf-8")
