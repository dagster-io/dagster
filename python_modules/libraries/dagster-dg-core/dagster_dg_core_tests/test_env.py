from pathlib import Path
from types import SimpleNamespace

from dagster_dg_core.env import ProjectEnvVars


def test_write_preserves_existing_dotenv_formatting(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "DAGSTER_HOME=/Users/king/.dagster/homes/example",
                "",
                "AWS_REGION=us-west-2",
                "AWS_PRIMARY_AVAILABILITY_ZONE_ID=usw2-az1",
                "",
                "SOURCE__SNOWFLAKE__HOST=somehost",
                "SOURCE__SNOWFLAKE__USERNAME=someuser",
                "SOURCE__SNOWFLAKE__PASSWORD=oldpassword",
            ]
        ),
        encoding="utf-8",
    )

    ctx = SimpleNamespace(is_project=True, root_path=tmp_path)

    ProjectEnvVars.from_ctx(ctx).with_values(
        {
            "AWS_REGION": "us-east-1",
            "SOURCE__SNOWFLAKE__PASSWORD": "somepassword",
            "NEW_SECRET": "newvalue",
        }
    ).write()

    assert env_path.read_text(encoding="utf-8") == "\n".join(
        [
            "DAGSTER_HOME=/Users/king/.dagster/homes/example",
            "",
            "AWS_REGION=us-east-1",
            "AWS_PRIMARY_AVAILABILITY_ZONE_ID=usw2-az1",
            "",
            "SOURCE__SNOWFLAKE__HOST=somehost",
            "SOURCE__SNOWFLAKE__USERNAME=someuser",
            "SOURCE__SNOWFLAKE__PASSWORD=somepassword",
            "NEW_SECRET=newvalue",
        ]
    )


def test_write_updates_assignment_when_key_also_appears_later_in_line(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("API_TOKEN=old # API_TOKEN\n", encoding="utf-8")

    ctx = SimpleNamespace(is_project=True, root_path=tmp_path)

    ProjectEnvVars.from_ctx(ctx).with_values({"API_TOKEN": "new"}).write()

    assert env_path.read_text(encoding="utf-8") == "API_TOKEN=new\n"


def test_write_preserves_crlf_when_appending_to_dotenv(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_bytes(b"API_TOKEN=old\r\n\r\nOTHER=value\r\n")

    ctx = SimpleNamespace(is_project=True, root_path=tmp_path)

    ProjectEnvVars.from_ctx(ctx).with_values({"API_TOKEN": "new", "NEW_SECRET": "newvalue"}).write()

    assert env_path.read_bytes() == b"API_TOKEN=new\r\n\r\nOTHER=value\r\nNEW_SECRET=newvalue\r\n"
