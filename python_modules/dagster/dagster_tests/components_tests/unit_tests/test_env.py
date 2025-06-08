from dagster.components.resolved.context import EnvScope
from dagster_shared.utils import environ


def test_env_syntaxs() -> None:
    with environ({"foo": "bar"}):
        env = EnvScope()
        assert env("foo") == "bar"
        assert env.foo == "bar"
        assert env("missing") is None
        assert env.missing is None
