from dagster.components.resolved.context import EnvTemplateVar
from dagster_shared.utils import environ


def test_env_syntaxs() -> None:
    with environ({"foo": "bar"}):
        env = EnvTemplateVar()
        assert env("foo") == "bar"
        assert env.foo == "bar"
        assert env("missing") is None
        assert env.missing is None
