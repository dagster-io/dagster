import pytest
from dagster import Definitions, EnvVar, RunConfig, asset
from dagster._config.pythonic_config import Config
from dagster._core.errors import DagsterInvalidConfigError
from dagster._core.test_utils import environ


def test_str_env_var() -> None:
    executed = {}

    class AStringConfig(Config):
        a_str: str

    @asset
    def a_string_asset(config: AStringConfig):
        assert config.a_str == "foo"
        executed["a_string_asset"] = True

    defs = Definitions(assets=[a_string_asset])

    with environ({"A_STR": "foo"}):
        defs.get_implicit_global_asset_job_def().execute_in_process(
            run_config=RunConfig(ops={"a_string_asset": AStringConfig(a_str=EnvVar("A_STR"))})
        )
    assert executed["a_string_asset"]


def test_str_env_var_nested() -> None:
    executed = {}

    class AStringConfig(Config):
        a_str: str

    class AnOuterConfig(Config):
        inner: AStringConfig

    @asset
    def a_string_asset(config: AnOuterConfig):
        assert config.inner.a_str == "bar"
        executed["a_string_asset"] = True

    defs = Definitions(assets=[a_string_asset])

    with environ({"A_STR": "bar"}):
        defs.get_implicit_global_asset_job_def().execute_in_process(
            run_config=RunConfig(
                ops={"a_string_asset": AnOuterConfig(inner=AStringConfig(a_str=EnvVar("A_STR")))}
            )
        )
    assert executed["a_string_asset"]


def test_int_env_var() -> None:
    executed = {}

    class AnIntConfig(Config):
        an_int: int

    @asset
    def an_int_asset(config: AnIntConfig):
        assert config.an_int == 5
        executed["an_int_asset"] = True

    defs = Definitions(assets=[an_int_asset])

    with environ({"AN_INT": "5"}):
        defs.get_implicit_global_asset_job_def().execute_in_process(
            run_config=RunConfig(ops={"an_int_asset": AnIntConfig(an_int=EnvVar.int("AN_INT"))})
        )
    assert executed["an_int_asset"]


def test_int_env_var_nested() -> None:
    executed = {}

    class AnIntConfig(Config):
        a_int: int

    class AnOuterConfig(Config):
        inner: AnIntConfig

    @asset
    def a_int_asset(config: AnOuterConfig):
        assert config.inner.a_int == 10
        executed["a_int_asset"] = True

    defs = Definitions(assets=[a_int_asset])

    with environ({"AN_INT": "10"}):
        defs.get_implicit_global_asset_job_def().execute_in_process(
            run_config=RunConfig(
                ops={"a_int_asset": AnOuterConfig(inner=AnIntConfig(a_int=EnvVar.int("AN_INT")))}
            )
        )
    assert executed["a_int_asset"]


def test_int_env_var_non_int_value() -> None:
    executed = {}

    class AnIntConfig(Config):
        an_int: int

    @asset
    def an_int_asset(config: AnIntConfig):
        assert config.an_int == 5
        executed["an_int_asset"] = True

    defs = Definitions(assets=[an_int_asset])

    with environ({"AN_INT": "NOT_AN_INT"}):
        with pytest.raises(
            DagsterInvalidConfigError,
            match=(
                'Value "NOT_AN_INT" stored in env variable "AN_INT" cannot be coerced into an int.'
            ),
        ):
            defs.get_implicit_global_asset_job_def().execute_in_process(
                run_config=RunConfig(ops={"an_int_asset": AnIntConfig(an_int=EnvVar.int("AN_INT"))})
            )
    assert len(executed) == 0
