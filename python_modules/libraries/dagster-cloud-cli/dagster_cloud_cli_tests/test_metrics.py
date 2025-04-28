import datetime
from typing import Optional
from unittest.mock import ANY, call

import freezegun
import pytest
import typer
from dagster_cloud_cli import ui
from dagster_cloud_cli.commands import metrics
from dagster_cloud_cli.config_utils import dagster_cloud_options
from dagster_cloud_cli.entrypoint import app
from dagster_cloud_cli.types import CliEventTags, CliEventType
from dagster_cloud_cli.utils import add_options
from typer.testing import CliRunner


@pytest.mark.parametrize(
    "envs, source",
    [
        ([], CliEventTags.source.cli),
        (["FOO"], CliEventTags.source.cli),
        (["GITHUB_ACTION"], CliEventTags.source.github),
        (["GITHUB_ACTION", "FOO"], CliEventTags.source.github),
        (["GITLAB_CI"], CliEventTags.source.gitlab),
        (["GITLAB_CI", "FOO"], CliEventTags.source.gitlab),
        (["GITHUB_ACTION", "GITLAB_CI"], CliEventTags.source.unknown),
    ],
)
def test_get_source(monkeypatch, envs, source):
    monkeypatch.delenv("BUILDKITE", raising=False)  # don't let buildkite testing break this test
    for env in envs:
        monkeypatch.setenv(env, "True")

    assert metrics.get_source() == source


def test_instrument(monkeypatch, mocker):
    monkeypatch.delenv("BUILDKITE", raising=False)  # don't let buildkite testing break this test

    with freezegun.freeze_time(datetime.datetime.now()) as frozen_datetime:
        gql = mocker.patch("dagster_cloud_cli.commands.metrics.gql", autospec=True)

        app = typer.Typer()

        unexpected = {"unexpected": (bool, typer.Option(False, "--unexpected"))}
        raising = {"raising": (bool, typer.Option(False, "--raising"))}

        @app.command(name="instrumented")
        @dagster_cloud_options(allow_empty=True, requires_url=True)
        @add_options(unexpected)
        @add_options(raising)
        @metrics.instrument(CliEventType.DEPLOY)
        def instrumented_command(
            api_token: str, url: str, unexpected: bool, raising: bool, **kwargs
        ):
            frozen_datetime.tick()
            if unexpected:
                raise Exception("bang")
            elif raising:
                raise ui.error("boom")
            else:
                ui.print("ok")

        @app.command(name="uninstrumented")
        @dagster_cloud_options(allow_empty=True, requires_url=True)
        @add_options(raising)
        def uninstrumented_command(api_token: str, url: str, raising: bool, **kwargs):
            frozen_datetime.tick()
            if raising:
                raise ui.error("boom")
            else:
                ui.print("ok")

        @app.command(name="instrumented-with-tags")
        @dagster_cloud_options(allow_empty=True, requires_url=True)
        @add_options(raising)
        @metrics.instrument(CliEventType.DEPLOY, tags=[CliEventTags.server_strategy.pex])
        def instrumented_with_tags_command(api_token: str, url: str, raising: bool, **kwargs):
            frozen_datetime.tick()
            if raising:
                raise ui.error("boom")
            else:
                ui.print("ok")
            metrics.instrument_add_tags([CliEventTags.source.bitbucket])

        env = {
            "DAGSTER_CLOUD_API_TOKEN": "fake-token",
            "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
            "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
        }

        env["DAGSTER_CLOUD_URL"] = "fake-url"

        result = CliRunner().invoke(app, ["instrumented"], env=env)
        assert result.exit_code == 0
        gql.mark_cli_event.assert_has_calls(
            [
                call(
                    client=ANY,
                    duration_seconds=1,
                    event_type=CliEventType.DEPLOY,
                    success=True,
                    tags=["source:cli"],
                ),
            ]
        )

        gql.reset_mock()
        result = CliRunner().invoke(app, ["instrumented", "--raising"], env=env)
        assert result.exit_code == 1
        gql.mark_cli_event.assert_has_calls(
            [
                call(
                    client=ANY,
                    duration_seconds=1,
                    event_type=CliEventType.DEPLOY,
                    success=False,
                    tags=["source:cli"],
                    message="boom",
                ),
            ]
        )

        gql.reset_mock()
        result = CliRunner().invoke(app, ["instrumented", "--unexpected"], env=env)
        assert result.exit_code == 1
        gql.mark_cli_event.assert_has_calls(
            [
                call(
                    client=ANY,
                    duration_seconds=1,
                    event_type=CliEventType.DEPLOY,
                    success=False,
                    tags=["source:cli"],
                    message="unexpected error",
                ),
            ]
        )

        gql.reset_mock()
        result = CliRunner().invoke(app, ["uninstrumented"], env=env)
        assert result.exit_code == 0
        gql.mark_cli_event.assert_not_called()

        gql.reset_mock()
        result = CliRunner().invoke(app, ["uninstrumented", "--raising"], env=env)
        assert result.exit_code == 1
        gql.mark_cli_event.assert_not_called()

        result = CliRunner().invoke(app, ["instrumented-with-tags"], env=env)
        assert result.exit_code == 0
        gql.mark_cli_event.assert_has_calls(
            [
                call(
                    client=ANY,
                    duration_seconds=1,
                    event_type=CliEventType.DEPLOY,
                    success=True,
                    # 'source:bitbucket' expected from the instrument_add_tags() call
                    tags=["server-strategy:pex", "source:cli", "source:bitbucket"],
                ),
            ]
        )

        # env is checked when the decorator executes, so we need a new command for GITHUB_ACTION
        monkeypatch.setenv("GITHUB_ACTION", "test-action")

        @app.command(name="instrumented-github")
        @dagster_cloud_options(allow_empty=True, requires_url=True)
        @metrics.instrument(CliEventType.DEPLOY)
        def github_instrumented_command(api_token: str, url: str, **kwargs):
            frozen_datetime.tick()
            ui.print("ok")

        gql.reset_mock()
        result = CliRunner().invoke(app, ["instrumented-github"], env=env)
        assert result.exit_code == 0, result.stdout_bytes.decode("utf-8")
        gql.mark_cli_event.assert_has_calls(
            [
                call(
                    client=ANY,
                    duration_seconds=1,
                    event_type=CliEventType.DEPLOY,
                    success=True,
                    tags=["source:github"],
                ),
            ]
        )


def test_all_instrumented_commands_have_urls(mocker):
    gql = mocker.patch("dagster_cloud_cli.commands.metrics.gql", autospec=True)

    env = {
        "DAGSTER_CLOUD_API_TOKEN": "fake-token",
        "DAGSTER_CLOUD_ORGANIZATION": "fake-organization",
        "DAGSTER_CLOUD_DEPLOYMENT": "fake-deployment",
    }

    def unwrap_func(func):
        if hasattr(func, "__wrapped__"):
            return unwrap_func(func.__wrapped__)
        return func

    def get_required_args(cmd):
        args = []
        for arg in unwrap_func(cmd.callback).__defaults__ or []:
            # ArgumentInfo implies positional arguments
            if isinstance(arg, typer.models.ArgumentInfo):
                # The positinal argument doesn't have a default
                if not arg.default or arg.default == ...:
                    # For tests, just pass the word "foo" to
                    # every required argument
                    args.append("foo")
        return args

    def walk_cli(obj, chain: Optional[list] = None):
        if not chain:
            chain = []

        for group in obj.registered_groups:
            walk_cli(group.typer_instance, chain + [group.name])
        for cmd in obj.registered_commands:
            cmd_name = cmd.name or cmd.callback.__name__

            command = chain + [cmd_name] + get_required_args(cmd)
            CliRunner().invoke(
                app,
                command,
                env=env,
            )

            # The command is instrumented
            if gql.mark_cli_event.called:
                # We cast the url to a string but we want to make sure
                # the original url isn't None

                # If this test fails, it's usually because the instrument
                # decorator is in the wrong place.
                url = gql.graphql_client_from_url.call_args_list[0].kwargs.get("url")
                assert "None" not in url, f"Command {command} wasn't provided a url"
                gql.mark_cli_event.reset_mock()
                gql.graphql_client_from_url.reset_mock()

    walk_cli(app)
