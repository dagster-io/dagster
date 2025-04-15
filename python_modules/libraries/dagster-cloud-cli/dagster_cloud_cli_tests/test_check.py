import os
import tempfile

from dagster_cloud_cli.entrypoint import app
from typer.testing import CliRunner, Result

EMPTY_DAGSTER_CLOUD_YAML = """
"""

INVALID_TOP_LEVEL_DAGSTER_CLOUD_YAML = """
a: b
"""


INVALID_LIST_DAGSTER_CLOUD_YAML = """
# locations is not a list
locations:
  location_name: quickstart_etl
  code_source:
    package_name: quickstart_etl
"""

INVALID_LOCATION_DAGSTER_CLOUD_YAML = """
locations:
  - location_name: quickstart_etl
    code_source:
      package_name: quickstart_etl
    b: c  # unexpected field
"""

DUP_LOCATION_DAGSTER_CLOUD_YAML = """
locations:
  - location_name: a
    code_source:
      package_name: a
  - location_name: a
    code_source:
      module_name: b
"""

LONG_VALID_DAGSTER_CLOUD_YAML = """
locations:
  - location_name: a
    code_source:
      package_name: a
  - location_name: b
    code_source:
      module_name: b
  - location_name: c
    code_source:
      module_name: c
    image: docker/c
    working_directory: c
  - location_name: d
    code_source:
      package_name: d
    build:
      directory: subdir
    image: docker/c
    agent_queue: my_queue
  - location_name: e
    code_source:
      package_name: e
    build:
      directory: subdir
    image: docker/e
    container_context:
      a: b
      c:
        d: e
        f: g
      h:
        - j
        - k
        - l

"""


def test_dagster_cloud_yaml_check() -> None:
    """Tests validation for dagster_cloud.yaml."""

    def check_yaml(text) -> Result:
        with tempfile.TemporaryDirectory() as tmpdir:
            os.mkdir(os.path.join(tmpdir, "subdir"))
            yaml_path = os.path.join(tmpdir, "dagster_cloud.yaml")
            with open(yaml_path, "w") as f:
                f.write(text)
            runner = CliRunner()
            return runner.invoke(
                app, ["ci", "check", "--project-dir", tmpdir, "--dagster-cloud-connect-check=skip"]
            )

    result = check_yaml(EMPTY_DAGSTER_CLOUD_YAML)
    assert result.exit_code
    assert "blank" in result.output

    result = check_yaml(INVALID_TOP_LEVEL_DAGSTER_CLOUD_YAML)
    assert result.exit_code

    # different err message for Pydantic 1 vs 2
    assert "unknown field" in result.output or ("Extra inputs are not permitted" in result.output)
    assert "missing" in result.output

    result = check_yaml(INVALID_LIST_DAGSTER_CLOUD_YAML)
    assert result.exit_code

    # different err message for Pydantic 1 vs 2
    assert "not a valid list" in result.output or ("Input should be a valid list" in result.output)

    result = check_yaml(INVALID_LOCATION_DAGSTER_CLOUD_YAML)
    assert result.exit_code

    # different err message for Pydantic 1 vs 2
    assert "unknown field" in result.output or ("Extra inputs are not permitted" in result.output)
    assert "locations.0.b" in result.output

    result = check_yaml(DUP_LOCATION_DAGSTER_CLOUD_YAML)
    assert result.exit_code

    # different err message for Pydantic 1 vs 2
    assert "duplicate location name" in result.output

    result = check_yaml(LONG_VALID_DAGSTER_CLOUD_YAML)
    assert not result.exit_code, result.output


def test_dagster_cloud_connect_check(empty_config, monkeypatch, mocker) -> None:
    """Tests connection check."""
    get_organization_settings = mocker.patch("dagster_cloud_cli.gql.get_organization_settings")

    def run_connect_check():
        with tempfile.TemporaryDirectory() as tmpdir:
            runner = CliRunner()
            return runner.invoke(
                app, ["ci", "check", "--project-dir", tmpdir, "--dagster-cloud-yaml-check=skip"]
            )

    result = run_connect_check()
    assert "organization" in result.output
    assert result.exit_code

    monkeypatch.setenv("DAGSTER_CLOUD_ORGANIZATION", "someorg")
    result = run_connect_check()
    assert "DAGSTER_CLOUD_API_TOKEN" in result.output
    assert result.exit_code

    monkeypatch.setenv("DAGSTER_CLOUD_API_TOKEN", "someorg:token")
    result = run_connect_check()
    assert "Able to connect to dagster.cloud" in result.output
    assert not result.exit_code
    get_organization_settings.assert_called_once()
